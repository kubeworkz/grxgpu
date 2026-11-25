#!/usr/bin/env bash
# =============================================================================
# rebuild-8x16.sh
#
# Fresh, user-space rebuild of the 8x16 Vortex GPGPU hierarchical RTLSIM model
# on the aarch64 build host (<instance-id>).  Nothing here needs root
# except the one-time partition/mount that must already have been done.
#
# Prerequisite on the host:
#   /home/ubuntu/vx is a mounted 400+ GiB filesystem.
#   The staged repo tarball is at $INCOMING/vortex-repo.tar.gz with a
#   sha256 file next to it:
#       cd /home/ubuntu/vx/incoming
#       sha256sum vortex-repo.tar.gz > vortex-repo.tar.gz.sha256
#
# Create the tarball on the workstation from the repo root (exclude .git and
# build outputs; include the ignored .buildonly overlay):
#   tar -czf vortex-repo.tar.gz \
#       --exclude=./.git --exclude='*/.git' \
#       --exclude=./build --exclude=./build32 --exclude=./build64 \
#       -C /path/to/grxgpu .
#   ssh -i ~/Downloads/<build-key>.pem ubuntu@<build-host> \
#       'mkdir -p /home/ubuntu/vx/incoming'
#   scp -i ~/Downloads/<build-key>.pem vortex-repo.tar.gz* \
#       ubuntu@<build-host>:/home/ubuntu/vx/incoming/
#
# Stages (run one at a time, or `all`):
#   preflight  toolchain  verilator  stage  configure  generate
#   launch     orchestrate  runtime  manifest  all
#
# Config evidence (2026-11-23):
#   Commit 0b7e42cd2 "Enable G100 config: 8 clusters x 16 cores, TCU/DXA/DSMEM"
#   changed only NUM_CLUSTERS 1->8 and NUM_CORES 1->16; SOCKET_SIZE stayed 1,
#   NUM_WARPS stayed 4, NUM_THREADS stayed 4, and L2_ENABLE stayed false.
#   The generated 8x16 headers in build32/ and build_wsl/ agree, and no
#   surviving log names an 8x16 override for those four fields.
#   The default profile is therefore g100-8x16: 8 clusters x 16 cores,
#   4 warps, 4 threads, socket 1, L2 off.  It is asserted against the staged
#   VX_config.toml, so a different TOML stops the build instead of drifting.
#   CONFIG_PROFILE=flagship is the separate, explicitly opt-in 64-warp /
#   32-thread / socket-4 / 8 MiB-L2 design-target preset; it is never the
#   repository default.  CONFIG_PROFILE=default is an alias for g100-8x16.
#
# The lost freeze/thaw orchestrator is replaced by an equivalent phased one:
# Verilator generates all child models first, then the two giant translation
# units per cluster are compiled serially under a flock + RAM gate + address
# space cap, and only then does the remaining model build run at -j$JOBS.
# This keeps the peak single-process footprint to one giant instead of
# racing the giant against 15 other jobs.  It is a new model, not the lost
# original, and the manifest records exactly what was built.
# =============================================================================

set -Eeuo pipefail

SELF=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd -- "$(dirname -- "$SELF")" && pwd)

DATA=${DATA:-/home/ubuntu/vx}
TOOLS=$DATA/tools
INCOMING=$DATA/incoming
REPO=$DATA/repo
BUILD=$DATA/build
MODEL=$DATA/model
LOGS=$DATA/logs

REPO_LINK=${REPO_LINK:-/home/ubuntu/vx-hier8x16-554e}
BUILD_LINK=${BUILD_LINK:-/home/ubuntu/vx-build-47822b9e}
REPO_TAR=${REPO_TAR:-$INCOMING/vortex-repo.tar.gz}
REPO_TAR_SHA=${REPO_TAR_SHA:-$REPO_TAR.sha256}

XLEN=${XLEN:-32}
JOBS=${JOBS:-16}
VERILATOR_JOBS=${VERILATOR_JOBS:-4}
CONFIG_PROFILE=${CONFIG_PROFILE:-g100-8x16}
FORCE=${FORCE:-0}
ARCHIVE_SKIP=${ARCHIVE_SKIP:-1}

GIANT_MIN_MB=${GIANT_MIN_MB:-100}
GIANT_MIN_AVAIL_MB=${GIANT_MIN_AVAIL_MB:-80000}
GIANT_ULIMIT_KB=${GIANT_ULIMIT_KB:-100000000}
HIER_MIN_AVAIL_MB=${HIER_MIN_AVAIL_MB:-20000}
STALL_MIN=${STALL_MIN:-20}
STALL_ACTION=${STALL_ACTION:-log}
# Verilator 5.054 implements the hierarchical interface/modport fixes, so the
# original modport directions can stay in the staged RTL.  Set to 0 only for
# older Verilator releases that reject a block-boundary interface drive.
KEEP_MODPORTS=${KEEP_MODPORTS:-1}

GCC_VER=16.2
VERILATOR_VER=5.054
# sha256 of https://github.com/verilator/verilator/archive/refs/tags/v5.054.tar.gz
VERILATOR_SHA256=18658731b46922ef660bcb650be0aa503d751e5c17eb9d4644fdfabb11835198
MAMBA_URL=https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-aarch64

STAGE=${1:-all}

# The profile and TOML are the single source of truth.  An inherited CONFIGS
# would override them inside the model/runtime makes and bypass the checks.
unset CONFIGS

# ---------------------------------------------------------------------------
# logging / small helpers
# ---------------------------------------------------------------------------
mkdir -p "$LOGS" 2>/dev/null || true
log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "${LOGS:-/tmp}/rebuild.log"; }
die() { log "ERROR: $*"; exit 1; }

trap 'rc=$?; printf "[%s] FAILED stage=%s line=%s rc=%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${STAGE:-init}" "$LINENO" "$rc" >&2' ERR

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }

mem_avail_mb() { awk '/^MemAvailable:/ {printf "%d", $2/1024}' /proc/meminfo; }

wait_mem() {
    local need=${1:-0} avail
    [ "$need" -le 0 ] && return 0
    while :; do
        avail=$(mem_avail_mb)
        if [ "$avail" -ge "$need" ]; then
            log "RAM gate OK: ${avail}MB available (need ${need}MB)"
            return 0
        fi
        log "RAM gate waiting: ${avail}MB available (need ${need}MB)"
        sleep 30
    done
}

ensure_link() {
    local link=$1 target=$2
    if [ -L "$link" ]; then
        ln -sfn "$target" "$link"
    elif [ -e "$link" ]; then
        die "$link exists and is not a symlink; inspect it instead of deleting it"
    else
        ln -s "$target" "$link"
    fi
}

mount_help() {
    cat >&2 <<'EOF'
/home/ubuntu/vx is not a mountpoint.  The build host needs the 500 GB data
partition mounted there first (this is the one privileged step; it is not
performed by this script):

  ssh -i ~/Downloads/<build-key>.pem ubuntu@<build-host>

  parted /dev/nvme0n1 unit GiB print free
  sudo parted /dev/nvme0n1 --script mkpart primary ext4 9GiB 100%
  sudo partprobe /dev/nvme0n1
  sudo mkfs.ext4 -m 0 -L vx /dev/nvme0n1p2
  sudo mkdir -p /home/ubuntu/vx
  sudo mount /dev/nvme0n1p2 /home/ubuntu/vx
  sudo chown ubuntu:ubuntu /home/ubuntu/vx
  df -h /home/ubuntu/vx

Then re-run this script.
EOF
}

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
run_preflight() {
    log "preflight: architecture, mount, memory, tools, tarball"
    [ "$(uname -m)" = "aarch64" ] || die "expected aarch64, got $(uname -m)"

    need_cmd mountpoint
    mountpoint -q "$DATA" || { mount_help; exit 2; }
    local avail_gb
    avail_gb=$(df -BG --output=avail "$DATA" | tail -1 | tr -dc '0-9')
    [ -n "$avail_gb" ] || die "could not read free space for $DATA"
    [ "$avail_gb" -ge 400 ] || die "$DATA has only ${avail_gb}G free; need at least 400G"

    local nproc mem_kb
    nproc=$(nproc)
    mem_kb=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
    [ "$nproc" -ge 16 ] || log "WARNING: only $nproc CPUs"
    [ "$mem_kb" -ge $((120 * 1024 * 1024)) ] || log "WARNING: less than 120 GiB RAM"

    local c
    for c in curl tar gzip git perl python3 sha256sum flock setsid timeout ps awk sed find xargs df mountpoint file; do
        need_cmd "$c"
    done

    [ -f "$REPO_TAR" ] || die "missing repo tarball: $REPO_TAR (see header for transfer command)"
    [ -f "$REPO_TAR_SHA" ] || die "missing sha256 file: $REPO_TAR_SHA"

    ( cd "$(dirname "$REPO_TAR")" \
      && tr -d '\r' < "$(basename "$REPO_TAR_SHA")" | sha256sum -c - ) \
        || die "repo tarball checksum mismatch"

    log "preflight OK: ${avail_gb}G free, ${nproc} CPUs, $((mem_kb / 1024 / 1024)) GiB RAM"
}

# ---------------------------------------------------------------------------
# user-space GCC 16.2 + build tools (micromamba, conda-forge)
# ---------------------------------------------------------------------------
run_toolchain() {
    log "toolchain: micromamba + GCC ${GCC_VER} + autoconf/flex/bison/make/cmake"
    mkdir -p "$TOOLS/bin" "$TOOLS/src" "$INCOMING" "$LOGS"

    if [ ! -x "$TOOLS/bin/micromamba" ]; then
        curl -fsSL "$MAMBA_URL" -o "$TOOLS/bin/micromamba"
        chmod +x "$TOOLS/bin/micromamba"
    fi
    "$TOOLS/bin/micromamba" --version

    export MAMBA_ROOT_PREFIX="$TOOLS/mamba"
    if [ ! -x "$TOOLS/conda/bin/aarch64-conda-linux-gnu-gcc" ] \
       || ! "$TOOLS/conda/bin/aarch64-conda-linux-gnu-gcc" --version | head -1 | grep -q "$GCC_VER"; then
        "$TOOLS/bin/micromamba" create -y -p "$TOOLS/conda" \
            --override-channels -c conda-forge \
            "gcc_linux-aarch64=${GCC_VER}" "gxx_linux-aarch64=${GCC_VER}" \
            make autoconf flex bison help2man perl pkg-config cmake ninja
    fi

    # The SoftFloat makefile invokes bare `gcc`, and ramulator's CMake invokes
    # bare `c++`; expose the conda compilers under those names in a private bin
    # directory rather than touching the system toolchain.
    local t src
    for t in gcc g++ cpp cc c++ ar ranlib nm objcopy strip ld as; do
        src="$TOOLS/conda/bin/aarch64-conda-linux-gnu-$t"
        if [ -x "$src" ]; then
            ln -sfn "$src" "$TOOLS/bin/$t"
        fi
    done

    cat > "$TOOLS/env.sh" <<EOF
export PATH="$TOOLS/bin:$TOOLS/conda/bin:\$PATH"
export CC="$TOOLS/bin/gcc"
export CXX="$TOOLS/bin/g++"
export MAMBA_ROOT_PREFIX="$TOOLS/mamba"
# ramulator's vendored yaml-cpp declares cmake_minimum_required(<3.5), which
# CMake 4 rejects; CMake 4 honors this variable for such projects.
export CMAKE_POLICY_VERSION_MINIMUM=3.5
EOF
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    "$CC" --version | head -1 | grep -q "$GCC_VER" || die "GCC is not $GCC_VER"
    "$CXX" --version | head -1 | grep -q "$GCC_VER" || die "G++ is not $GCC_VER"
    for c in make autoconf flex bison help2man cmake; do
        need_cmd "$c"
    done
    log "toolchain OK: $("$CC" --version | head -1)"
    log "toolchain OK: $(make --version | head -1)"
}

# ---------------------------------------------------------------------------
# Verilator 5.042 from source, installed under $TOOLS
# ---------------------------------------------------------------------------
run_verilator() {
    log "verilator: build ${VERILATOR_VER} from pinned tarball"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    local prefix="$TOOLS/verilator-${VERILATOR_VER}"
    if [ ! -x "$prefix/bin/verilator" ] \
       || ! "$prefix/bin/verilator" --version | grep -q "$VERILATOR_VER"; then
        mkdir -p "$TOOLS/src"
        cd "$TOOLS/src"
        if [ ! -f "v${VERILATOR_VER}.tar.gz" ]; then
            curl -fsSL -o "v${VERILATOR_VER}.tar.gz" \
                "https://github.com/verilator/verilator/archive/refs/tags/v${VERILATOR_VER}.tar.gz"
        fi
        echo "${VERILATOR_SHA256}  v${VERILATOR_VER}.tar.gz" | sha256sum -c - \
            || die "Verilator tarball checksum mismatch"
        rm -rf "verilator-${VERILATOR_VER}"
        tar -xzf "v${VERILATOR_VER}.tar.gz"
        cd "verilator-${VERILATOR_VER}"
        autoconf
        # conda's flex ships FlexLexer.h under $TOOLS/conda/include, which the
        # cross toolchain does not search; expose only that header, not the
        # whole conda include tree, so sysroot headers keep precedence.
        mkdir -p "$TOOLS/flex-include"
        ln -sfn "$TOOLS/conda/include/FlexLexer.h" "$TOOLS/flex-include/FlexLexer.h"
        CPPFLAGS="-I$TOOLS/flex-include" ./configure --prefix="$prefix" CC="$CC" CXX="$CXX"
        make -j"$(nproc)"
        make install
    fi

    ln -sfn "$prefix" "$TOOLS/verilator"
    if [ -e "/tmp/verilator-${VERILATOR_VER}" ] && [ ! -L "/tmp/verilator-${VERILATOR_VER}" ]; then
        die "/tmp/verilator-${VERILATOR_VER} exists and is not a symlink"
    fi
    ln -sfn "$prefix" "/tmp/verilator-${VERILATOR_VER}"

    "$prefix/bin/verilator" --version | grep -q "$VERILATOR_VER" \
        || die "Verilator is not $VERILATOR_VER"
    "$prefix/bin/verilator" --help 2>&1 | grep -q -- '--hierarchical-threads' \
        || die "Verilator $VERILATOR_VER lacks --hierarchical-threads"
    log "verilator OK: $("$prefix/bin/verilator" --version)"
}

# ---------------------------------------------------------------------------
# staged repo: extract, apply the build-only flat overlay, build third_party
# ---------------------------------------------------------------------------
apply_flagship_config() {
    log "config: applying documented flagship preset to the staged VX_config.toml"
    python3 - "$REPO/VX_config.toml" <<'PY'
import sys

path = sys.argv[1]
want = {
    "VX_CFG_NUM_CLUSTERS": "8",
    "VX_CFG_NUM_CORES": "16",
    "VX_CFG_SOCKET_SIZE": "4",
    "VX_CFG_NUM_WARPS": "64",
    "VX_CFG_NUM_THREADS": "32",
    "VX_CFG_L2_ENABLE": "true",
    "VX_CFG_L2_SIZE": "8388608",
    "VX_CFG_EXT_TCU_ENABLE": "true",
    "VX_CFG_TCU_TF32_ENABLE": "true",
    "VX_CFG_TCU_FP8_ENABLE": "true",
    "VX_CFG_TCU_INT8_ENABLE": "true",
    "VX_CFG_TCU_MX_ENABLE": "true",
    "VX_CFG_TCU_SPARSE_ENABLE": "true",
    "VX_CFG_TCU_WGMMA_ENABLE": "true",
}

with open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

seen = set()
out = []
for line in lines:
    stripped = line.split("#", 1)[0]
    key = None
    for k in want:
        if stripped.lstrip().startswith(k + " ") or stripped.lstrip().startswith(k + "="):
            key = k
            break
    if key is None:
        out.append(line)
        continue
    newline = ""
    body = line
    if body.endswith("\r\n"):
        newline, body = "\r\n", body[:-2]
    elif body.endswith("\n"):
        newline, body = "\n", body[:-1]
    indent = body[:len(body) - len(body.lstrip())]
    out.append(f"{indent}{key} = {want[key]}{newline}")
    seen.add(key)

missing = set(want) - seen
if missing:
    raise SystemExit("missing VX_config.toml keys: " + ", ".join(sorted(missing)))

with open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(out)
PY
}

verify_8x16_config() {
    # Repository evidence for the 8x16 model: 0b7e42cd2 ("Enable G100 config:
    # 8 clusters x 16 cores, TCU/DXA/DSMEM") changed only NUM_CLUSTERS and
    # NUM_CORES; SOCKET_SIZE stayed 1, NUM_WARPS stayed 4, NUM_THREADS stayed
    # 4, and L2_ENABLE stayed false.  The generated 8x16 headers under build32/
    # and build_wsl/ agree.  Assert the staged TOML rather than trusting the
    # current default.
    local toml="$REPO/VX_config.toml" spec key val
    for spec in \
        "VX_CFG_NUM_CLUSTERS:8" \
        "VX_CFG_NUM_CORES:16" \
        "VX_CFG_SOCKET_SIZE:1" \
        "VX_CFG_NUM_WARPS:4" \
        "VX_CFG_NUM_THREADS:4" \
        "VX_CFG_L2_ENABLE:false"; do
        key=${spec%%:*}
        val=${spec##*:}
        grep -Eq "^[[:space:]]*${key}[[:space:]]*=[[:space:]]*${val}[[:space:]]*(#.*)?$" "$toml" \
            || die "8x16 config mismatch in $toml: $key must be $val (evidence: commit 0b7e42cd2; generated 8x16 headers in build32/ and build_wsl/)"
    done
    log "config evidence OK: 8 clusters x 16 cores, socket 1, 4 warps, 4 threads, L2 off (commit 0b7e42cd2)"
}

run_stage() {
    log "stage: extract repo and apply build-only hierarchical overlay"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    mkdir -p "$REPO" "$BUILD" "$MODEL"
    if [ ! -f "$REPO/.staged-ok" ]; then
        [ -z "$(ls -A "$REPO" 2>/dev/null)" ] \
            || die "$REPO is non-empty but has no .staged-ok marker; inspect it"
        tar -xzf "$REPO_TAR" -C "$REPO"
        touch "$REPO/.staged-ok"
    else
        log "stage: repo already extracted, reusing"
    fi

    [ -f "$REPO/VX_config.toml" ] || die "staged repo is missing VX_config.toml"
    [ -f "$REPO/.buildonly/VX_cluster_flat.sv" ] \
        || die "staged repo is missing .buildonly/VX_cluster_flat.sv"
    [ -f "$REPO/.buildonly/VX_cluster.sv" ] \
        || die "staged repo is missing .buildonly/VX_cluster.sv"

    # The flat block is a facade over the existing cluster implementation.
    # Preserve the original module as VX_cluster_impl, then replace the
    # in-tree VX_cluster with the interface-preserving facade.  This is a
    # build-only overlay in the staged tree; the committed RTL is untouched.
    if [ ! -f "$REPO/hw/rtl/VX_cluster_impl.sv" ]; then
        cp "$REPO/hw/rtl/VX_cluster.sv" "$REPO/hw/rtl/VX_cluster_impl.sv"
        sed -i '0,/^module VX_cluster /s//module VX_cluster_impl /' \
            "$REPO/hw/rtl/VX_cluster_impl.sv"
    fi
    grep -q '^module VX_cluster_impl ' "$REPO/hw/rtl/VX_cluster_impl.sv" \
        || die "VX_cluster_impl rename failed"
    # Verilator's hierarchical block compilation applies a child port's modport
    # to the enclosing interface instance, so a facade drive can read as a
    # write to an input.  Older releases need the hints dropped; 5.054's
    # interface fixes keep them without changing connectivity.
    if [ "$KEEP_MODPORTS" != "1" ]; then
        find "$REPO/hw/rtl" -type f -name '*.sv' -exec sed -i -E \
            's/\b(VX_(dcr|mem|kmu|gbar)_bus_if|VX_raster_launch_if)\.(slave|master)\b/\1/g' {} +
    fi
    cp "$REPO/.buildonly/VX_cluster.sv" "$REPO/hw/rtl/VX_cluster.sv"
    cp "$REPO/.buildonly/VX_cluster_flat.sv" "$REPO/hw/rtl/VX_cluster_flat.sv"

    local toml="$REPO/VX_config.toml"
    if [ ! -f "$REPO/.buildonly/VX_config.toml.orig" ]; then
        cp "$toml" "$REPO/.buildonly/VX_config.toml.orig"
    fi
    case "$CONFIG_PROFILE" in
        g100-8x16|default)
            cp "$REPO/.buildonly/VX_config.toml.orig" "$toml"
            verify_8x16_config ;;
        flagship)
            cp "$REPO/.buildonly/VX_config.toml.orig" "$toml"
            apply_flagship_config ;;
        *)
            die "unknown CONFIG_PROFILE=$CONFIG_PROFILE (g100-8x16|default|flagship)" ;;
    esac

    ensure_link "$REPO_LINK" "$REPO"
    ensure_link "$BUILD_LINK" "$BUILD"

    # A prebuilt x86_64 libramulator or SoftFloat archive from the checkout
    # would make make skip the rebuild; remove only those generated files.
    rm -rf "$REPO/third_party/ramulator/build"
    rm -f "$REPO/third_party/ramulator/libramulator.so"
    rm -f "$REPO/third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a"
    rm -f "$REPO/third_party/softfloat/build/Linux-x86_64-GCC/"*.o

    log "stage: building softfloat + ramulator with the conda toolchain"
    # Ramulator's vendored yaml-cpp relies on a transitive <cstdint>, which
    # GCC 16's libstdc++ no longer provides; force the header for its C++
    # compiles only, leaving the vendored sources untouched.
    CXXFLAGS="${CXXFLAGS:-} -include cstdint" \
        make -C "$REPO/third_party" -j"$(nproc)" softfloat ramulator \
        2>&1 | tee "$LOGS/third_party.log"

    [ -f "$REPO/third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a" ] \
        || die "softfloat.a was not produced"
    [ -f "$REPO/third_party/ramulator/libramulator.so" ] \
        || die "libramulator.so was not produced"
    log "stage: third_party OK"
}

# ---------------------------------------------------------------------------
# configure + build-only Makefile/control-file patches
# ---------------------------------------------------------------------------
run_configure() {
    log "configure: XLEN=${XLEN} TOOLDIR=${TOOLS} profile=${CONFIG_PROFILE}"
    case "$CONFIG_PROFILE" in
        g100-8x16|default|flagship) ;;
        *) die "unknown CONFIG_PROFILE=$CONFIG_PROFILE (g100-8x16|default|flagship)" ;;
    esac
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    # The profile restore preserves the archived TOML's mtime, and configure
    # regenerates the headers only when the TOML is newer.  Force it.
    touch "$REPO/VX_config.toml"

    mkdir -p "$BUILD"
    cd "$BUILD"
    # Ubuntu 26.04 (resolute) is not in configure's codename table, which
    # already maps jammy/noble to ubuntu/focal for the prebuilt toolchain
    # layout; pass the same value explicitly.
    "$REPO/configure" --xlen="$XLEN" --tooldir="$TOOLS" --osversion=ubuntu/focal \
        2>&1 | tee "$LOGS/configure.log"

    local exp_clusters=8 exp_cores=16 exp_warps=4 exp_threads=4 exp_socket=1 exp_l2=0
    if [ "$CONFIG_PROFILE" = "flagship" ]; then
        exp_warps=64 exp_threads=32 exp_socket=4 exp_l2=1
    fi

    local hdr="$BUILD/sw/VX_config.h"
    [ -f "$hdr" ] || die "configure did not generate $hdr"

    # gen_config.py is the resolver the build uses.  Its resolved cflags are
    # authoritative; the header's VX_CFG_L2_ENABLED is an #ifdef with both 1
    # and 0 present as text, so grepping the header cannot prove L2 is off.
    local resolved spec key val
    resolved=$(python3 "$REPO/ci/gen_config.py" \
        --config="$REPO/VX_config.toml" \
        --cflags="-DVX_CFG_XLEN=$XLEN") \
        || die "gen_config.py failed for $REPO/VX_config.toml"
    for spec in \
        "VX_CFG_NUM_CLUSTERS:$exp_clusters" \
        "VX_CFG_NUM_CORES:$exp_cores" \
        "VX_CFG_NUM_WARPS:$exp_warps" \
        "VX_CFG_NUM_THREADS:$exp_threads" \
        "VX_CFG_SOCKET_SIZE:$exp_socket" \
        "VX_CFG_L2_ENABLED:$exp_l2"; do
        key=${spec%%:*}
        val=${spec##*:}
        printf '%s\n' "$resolved" | tr -s '[:space:]' '\n' \
            | grep -qx -- "-D${key}=${val}" \
            || die "resolved config mismatch: $key != $val"
    done

    local mk="$BUILD/sim/rtlsim/Makefile"
    [ -f "$mk" ] || die "configure did not copy sim/rtlsim/Makefile"
    if ! grep -q -- '--hierarchical' "$mk"; then
        awk '
            /^VL_FLAGS \+= -O1$/ {
                print;
                print "VL_FLAGS += --hierarchical";
                print "VL_FLAGS += --hierarchical-threads 1";
                print "VL_FLAGS += --output-split 10000";
                next
            }
            { print }
        ' "$mk" > "$mk.hier"
        # Verilator 5.042's --cc takes no prefix argument.  The Makefile's
        # bare $(TOP) only resolves through the -I extension search, which
        # the hierarchical makefile cannot stat as a prerequisite; pass the
        # real source path instead.
        sed -i 's|--cc \$(TOP) --top-module|--cc $(SRC_DIR)/$(TOP).sv --top-module|' "$mk.hier"
    else
        cp "$mk" "$BUILD/sim/rtlsim/Makefile.hier"
    fi
    grep -q -- '--hierarchical-threads 1' "$BUILD/sim/rtlsim/Makefile.hier" \
        || die "failed to add hierarchical flags to Makefile.hier"
    grep -q -- '--output-split 10000' "$BUILD/sim/rtlsim/Makefile.hier" \
        || die "failed to add --output-split to Makefile.hier"

    local vlt="$BUILD/sim/rtlsim/verilator.vlt"
    [ -f "$vlt" ] || die "configure did not generate verilator.vlt"
    grep -q 'hier_block -module "VX_cluster_flat"' "$vlt" \
        || echo 'hier_block -module "VX_cluster_flat"' >> "$vlt"
    grep -q 'hier_block -module "VX_cluster_flat"' "$vlt" \
        || die "failed to mark VX_cluster_flat as a hierarchy block"

    # The runtime's driver rule must reuse the hierarchical model.  Without
    # -f Makefile.hier it would see different VL_FLAGS, regenerate the model,
    # and wipe the obj_dir the orchestrator just populated.
    local rtmk="$BUILD/sw/runtime/rtlsim/Makefile"
    [ -f "$rtmk" ] || die "configure did not copy sw/runtime/rtlsim/Makefile"
    python3 - "$rtmk" <<'PY'
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# The model's CONFIG_FILE stamp includes VL_FLAGS, whose -j value is
# $(THREADS).  If the runtime sub-make used its CPU-count default it would
# see a different stamp and wipe the hierarchical obj_dir.  Pin both sides to
# the same value.
if "RT_THREADS ?=" not in text:
    if "include ../common.mk\n" not in text:
        raise SystemExit("runtime Makefile include not found")
    text = text.replace("include ../common.mk\n",
                        "include ../common.mk\n\nRT_THREADS ?= 4\n", 1)

old = "$(MAKE) -C $(ROOT_DIR)/sim/rtlsim $(DESTDIR)/librtlsim.so"
new = "$(MAKE) -C $(ROOT_DIR)/sim/rtlsim -f Makefile.hier THREADS=$(RT_THREADS) $(DESTDIR)/librtlsim.so"
if old in text:
    text = text.replace(old, new)
elif new not in text:
    raise SystemExit("runtime driver rule not found")
text = text.replace(old, new)

old2 = "DESTDIR=$(DESTDIR) $(MAKE) -C $(ROOT_DIR)/sim/rtlsim verilate"
new2 = "DESTDIR=$(DESTDIR) $(MAKE) -C $(ROOT_DIR)/sim/rtlsim -f Makefile.hier THREADS=$(RT_THREADS) verilate"
text = text.replace(old2, new2)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
PY
    grep -q -- '-f Makefile.hier' "$rtmk" \
        || die "failed to point the runtime driver rule at Makefile.hier"

    {
        echo "profile=$CONFIG_PROFILE"
        echo "XLEN=$XLEN"
        echo "JOBS=$JOBS"
        echo "VERILATOR_JOBS=$VERILATOR_JOBS"
        echo "TOOLDIR=$TOOLS"
        echo "VORTEX_HOME=$REPO"
        echo "BUILDDIR=$BUILD"
        echo "generated=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        if [ "$CONFIG_PROFILE" = "flagship" ]; then
            echo "profile_source=documented G100 flagship design-target preset"
        else
            echo "profile_source=commit 0b7e42cd2: 8x16 enabled by changing clusters/cores only; 4 warps/4 threads/socket 1/L2 off retained"
        fi
        echo "VX_CFG_NUM_CLUSTERS=$exp_clusters"
        echo "VX_CFG_NUM_CORES=$exp_cores"
        echo "VX_CFG_NUM_WARPS=$exp_warps"
        echo "VX_CFG_NUM_THREADS=$exp_threads"
        echo "VX_CFG_SOCKET_SIZE=$exp_socket"
        echo "VX_CFG_L2_ENABLED=$exp_l2"
    } > "$BUILD/config-used.txt"
    log "configure OK: 8x16 profile=$CONFIG_PROFILE"
}

# ---------------------------------------------------------------------------
# hierarchical Verilator generation (no C++ compilation)
# ---------------------------------------------------------------------------
run_generate() {
    log "generate: Verilator --hierarchical, 8 child models"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    mkdir -p "$MODEL"
    local obj="$MODEL/librtlsim.so.obj_dir"
    local hier="$obj/Vrtlsim_shim_hier.mk"

    if [ -f "$hier" ] && [ "$FORCE" != "1" ]; then
        local stamp="$MODEL/rtlsim_config.stamp"
        if [ -f "$stamp" ] \
           && ! grep -Eq -- "-j ${VERILATOR_JOBS}([[:space:]]|$)" "$stamp"; then
            die "existing model was generated with a different THREADS; use FORCE=1 or the original VERILATOR_JOBS"
        fi
        log "generate: existing hierarchical model found, skipping Verilation"
    else
        if [ "$FORCE" = "1" ]; then
            log "generate: FORCE=1, removing generated model directory $obj"
            rm -rf "$obj"
        fi
        wait_mem 100000
        make -C "$BUILD/sim/rtlsim" -f Makefile.hier \
            "$obj/Vrtlsim_shim.mk" \
            DESTDIR="$MODEL" THREADS="$VERILATOR_JOBS" \
            2>&1 | tee "$LOGS/generate.log"
    fi

    [ -f "$hier" ] || die "missing $hier"
    [ -f "$obj/Vrtlsim_shim.mk" ] || die "missing $obj/Vrtlsim_shim.mk"

    local children=()
    mapfile -t children < <(find "$obj" -maxdepth 1 -mindepth 1 -type d \
        ! -name 'Vrtlsim_shim*' -print)
    [ "${#children[@]}" -eq 8 ] \
        || die "expected 8 child model directories, found ${#children[@]} in $obj"

    : > "$LOGS/generation-counts.txt"
    local d
    for d in "${children[@]}"; do
        printf '%s\t%s .cpp\n' "$(basename "$d")" \
            "$(find "$d" -maxdepth 1 -type f -name '*.cpp' | wc -l)" \
            >> "$LOGS/generation-counts.txt"
    done
    find "$obj" -mindepth 2 -maxdepth 2 -type f -name '*.cpp' \
        -size +"${GIANT_MIN_MB}"M -printf '%s %p\n' \
        | sort -rn >> "$LOGS/generation-counts.txt"
    log "generate OK: ${#children[@]} children; counts in $LOGS/generation-counts.txt"
}

# ---------------------------------------------------------------------------
# oracle: compile the giant translation units one at a time
# ---------------------------------------------------------------------------
monitor_stall() {
    local pid=$1 cpp=$2 pat prev=-1 idle=0 ticks p
    pat=$(basename "$cpp")
    while kill -0 "$pid" 2>/dev/null; do
        sleep 60
        ticks=0
        for p in $(pgrep -f -- "$pat" 2>/dev/null || true); do
            [ -r "/proc/$p/stat" ] || continue
            ticks=$((ticks + $(awk '{print $14 + $15}' "/proc/$p/stat" 2>/dev/null || echo 0)))
        done
        if [ "$ticks" -eq "$prev" ]; then
            idle=$((idle + 1))
        else
            idle=0
            prev=$ticks
        fi
        if [ "$idle" -ge "$STALL_MIN" ]; then
            log "STALL: no compiler CPU progress for ${STALL_MIN}m on $pat (ticks=$ticks)"
            if [ "$STALL_ACTION" = "stop" ]; then
                kill -TERM "$pid" 2>/dev/null || true
            fi
            return 0
        fi
    done
}

compile_giant() {
    local child=$1 mk=$2 obj=$3
    local cpp="${obj%.o}.cpp"
    local logf="$LOGS/giant-$(basename "$obj").log"
    local marker="${obj}.ok"
    local pat
    pat=$(basename "$cpp")

    # A marker is minted only after a successful make and a non-empty object.
    # It is removed before every compile, so a killed compile leaves the
    # object without a marker and resume rebuilds instead of trusting it.
    if [ -s "$obj" ] && [ -f "$marker" ] \
       && [ "$marker" -nt "$obj" ] && [ "$obj" -nt "$cpp" ]; then
        log "giant skip (completed object): $(basename "$obj")"
        return 0
    fi
    # Concurrent-giant guard: no other compiler should be chewing on this TU.
    if ps -eo pid,args --no-headers | grep -F -- "$pat" | grep -vE 'grep|pgrep' >/dev/null; then
        die "another process is already compiling $pat"
    fi

    # make would treat an existing object as current; remove it so a retry
    # cannot skip the rebuild and mint a marker for a partial object.
    rm -f "$obj" "$marker"

    wait_mem "$GIANT_MIN_AVAIL_MB"
    log "giant start: $(basename "$obj") source=$(stat -c%s "$cpp") bytes"

    local tcmd=()
    [ -x /usr/bin/time ] && tcmd=(/usr/bin/time -v)

    (
        if [ "$GIANT_ULIMIT_KB" -gt 0 ]; then
            ulimit -v "$GIANT_ULIMIT_KB"
        fi
        cd "$child"
        "${tcmd[@]}" make -f "$(basename "$mk")" -j1 "$(basename "$obj")"
    ) > "$logf" 2>&1 &
    local pid=$!
    monitor_stall "$pid" "$cpp" &
    local mpid=$!

    local rc=0
    wait "$pid" || rc=$?
    kill "$mpid" 2>/dev/null || true
    wait "$mpid" 2>/dev/null || true

    if [ "$rc" -ne 0 ]; then
        tail -80 "$logf" || true
        die "giant compile failed: $(basename "$obj") (log $logf)"
    fi
    [ -s "$obj" ] || die "giant compiler returned success but $obj is empty"
    touch "$marker"

    local rss
    rss=$(awk '/Maximum resident set size/ {print $NF}' "$logf" | tail -1)
    printf '%s\t%s\t%s\n' "$(basename "$obj")" "${rss:-unknown}" \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGS/giant-memory.tsv"
    log "giant done: $(basename "$obj") maxrss=${rss:-unknown}KB"
}

run_orchestrate() {
    log "orchestrate: phased giant-TU build for 8 children"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    local obj="$MODEL/librtlsim.so.obj_dir"
    local hier="$obj/Vrtlsim_shim_hier.mk"
    [ -f "$hier" ] || die "missing $hier; run the generate stage first"

    exec 9>"$DATA/.orchestrator.lock"
    flock -n 9 || die "another orchestrator holds $DATA/.orchestrator.lock"

    if [ "$ARCHIVE_SKIP" = "1" ] && [ -s "$MODEL/librtlsim.so" ]; then
        log "ARCHIVE_SKIP: $MODEL/librtlsim.so already exists"
    else
        local giants=()
        mapfile -t giants < <(
            find "$obj" -mindepth 2 -maxdepth 2 -type f -name '*.cpp' \
                -size +"${GIANT_MIN_MB}"M -printf '%s\t%p\n' \
                | sort -rn | cut -f2-
        )
        log "orchestrate: ${#giants[@]} giant translation units"

        local cpp child mk giant_obj
        for cpp in "${giants[@]}"; do
            child=$(dirname "$cpp")
            mk=$(find "$child" -maxdepth 1 -type f -name '*.mk' \
                ! -name 'verilated.mk' | head -1)
            [ -n "$mk" ] || die "no model makefile in $child"
            giant_obj="${cpp%.cpp}.o"
            compile_giant "$child" "$mk" "$giant_obj"
        done

        wait_mem "$HIER_MIN_AVAIL_MB"
        log "orchestrate: remaining model build at -j${JOBS}"
        make -C "$obj" -f "$(basename "$hier")" -j"$JOBS" hier_build \
            2>&1 | tee "$LOGS/hier-build.log" \
            || die "hier_build failed (see $LOGS/hier-build.log)"

        if [ ! -s "$MODEL/librtlsim.so" ]; then
            log "orchestrate: hier_build did not link the top library; trying the top makefile"
            make -C "$obj" -f Vrtlsim_shim.mk -j"$JOBS" \
                2>&1 | tee -a "$LOGS/hier-build.log" \
                || die "top model link failed"
        fi
    fi

    [ -s "$MODEL/librtlsim.so" ] || die "missing $MODEL/librtlsim.so"
    log "orchestrate OK: $MODEL/librtlsim.so"

    "$SELF" runtime
    "$SELF" manifest
}

# ---------------------------------------------------------------------------
# launch the orchestrator detached
# ---------------------------------------------------------------------------
run_launch() {
    log "launch: starting orchestrator in a new session"
    mkdir -p "$LOGS"
    # The detached orchestrator must see the same build shape as this shell.
    export DATA TOOLS INCOMING REPO BUILD MODEL LOGS
    export XLEN JOBS VERILATOR_JOBS CONFIG_PROFILE FORCE ARCHIVE_SKIP
    export GIANT_MIN_MB GIANT_MIN_AVAIL_MB GIANT_ULIMIT_KB HIER_MIN_AVAIL_MB
    export STALL_MIN STALL_ACTION
    if [ -f "$LOGS/orchestrator.pid" ]; then
        local old
        old=$(cat "$LOGS/orchestrator.pid" 2>/dev/null || true)
        if [ -n "$old" ] && kill -0 "$old" 2>/dev/null; then
            die "orchestrator already running as pid $old"
        fi
    fi
    setsid nohup "$SELF" orchestrate >> "$LOGS/orchestrator.log" 2>&1 < /dev/null &
    local pid=$!
    echo "$pid" > "$LOGS/orchestrator.pid"
    log "launch OK: pid=$pid log=$LOGS/orchestrator.log"
    log "follow with: tail -f $LOGS/orchestrator.log"
}

# ---------------------------------------------------------------------------
# host runtime library
# ---------------------------------------------------------------------------
run_runtime() {
    log "runtime: build libvortex-rtlsim.so"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    make -C "$BUILD/sw/runtime/rtlsim" -j"$JOBS" DESTDIR="$MODEL" \
        RT_THREADS="$VERILATOR_JOBS" \
        2>&1 | tee "$LOGS/runtime.log" \
        || die "runtime build failed (see $LOGS/runtime.log)"

    [ -s "$MODEL/libvortex-rtlsim.so" ] \
        || die "missing $MODEL/libvortex-rtlsim.so"
    file "$MODEL/librtlsim.so" "$MODEL/libvortex-rtlsim.so" | tee -a "$LOGS/runtime.log"
    log "runtime OK: $MODEL/libvortex-rtlsim.so"
}

# ---------------------------------------------------------------------------
# manifest for the new model (no claim of parity with the lost original)
# ---------------------------------------------------------------------------
run_manifest() {
    log "manifest: recording toolchain, config and artifact hashes"
    # shellcheck disable=SC1090
    source "$TOOLS/env.sh"

    local obj="$MODEL/librtlsim.so.obj_dir"
    local cfg="$BUILD/config-used.txt"
    [ -f "$cfg" ] || die "missing $cfg; run the configure stage first"
    local profile
    profile=$(sed -n 's/^profile=//p' "$cfg" | head -1)
    {
        echo "# Fresh 8x16 hierarchical RTLSIM model (not the lost original)"
        echo "generated=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "profile=${profile:-unknown}"
        echo "repo=$REPO"
        echo "build=$BUILD"
        echo "model=$MODEL"
        echo
        echo "## toolchain"
        "$TOOLS/verilator-${VERILATOR_VER}/bin/verilator" --version
        "$CC" --version | head -1
        "$CXX" --version | head -1
        make --version | head -1
        echo
        echo "## configuration"
        cat "$cfg"
        sha256sum "$REPO/VX_config.toml" \
                  "$BUILD/sim/rtlsim/Makefile.hier" \
                  "$BUILD/sim/rtlsim/verilator.vlt" \
                  "$cfg"
        echo
        echo "## third_party"
        sha256sum "$REPO/third_party/softfloat/build/Linux-x86_64-GCC/softfloat.a" \
                  "$REPO/third_party/ramulator/libramulator.so"
        echo
        echo "## child models"
        find "$obj" -maxdepth 1 -mindepth 1 -type d ! -name 'Vrtlsim_shim*' \
            -printf '%f\n' | sort
        echo
        echo "## giant memory (object, maxrss_kb, finished_utc)"
        cat "$LOGS/giant-memory.tsv" 2>/dev/null || echo "none"
    } > "$MODEL/manifest.txt"

    ( cd "$MODEL" && sha256sum librtlsim.so libvortex-rtlsim.so > SHA256SUMS )
    log "manifest OK: $MODEL/manifest.txt"
    log "artifacts:"
    ( cd "$MODEL" && cat SHA256SUMS )
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
usage() {
    sed -n '2,/^set -Eeuo pipefail$/p' "$SELF" | sed '$d'
    exit 1
}

run_all() {
    run_preflight
    run_toolchain
    run_verilator
    run_stage
    run_configure
    run_generate
    run_launch
}

# Resuming a single stage after a reboot must not write build output to the
# 6.8 GiB root filesystem; every non-preflight stage requires the data mount.
case "$STAGE" in
    preflight|help|-h|--help) ;;
    *) mountpoint -q "$DATA" || { mount_help; exit 2; } ;;
esac

case "$STAGE" in
    preflight)   run_preflight ;;
    toolchain)   run_toolchain ;;
    verilator)   run_verilator ;;
    stage)       run_stage ;;
    configure)   run_configure ;;
    generate)    run_generate ;;
    orchestrate) run_orchestrate ;;
    launch)      run_launch ;;
    runtime)     run_runtime ;;
    manifest)    run_manifest ;;
    all)         run_all ;;
    -h|--help|help) usage ;;
    *) echo "unknown stage: $STAGE" >&2; usage ;;
esac
