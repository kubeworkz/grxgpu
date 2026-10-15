# Local GF180MCU Flow Environment

The current WSL environment has an isolated flow root at `/home/kubew/g100-gf180-tools`. It contains the pinned GF180MCU PDK release and a helper environment file; no system package installation or global shell profile changes are needed.

## Activate the environment

```bash
source /home/kubew/g100-gf180-tools/env.sh
```

This exports `PDK_ROOT`, `VOLARE_HOME`, the Docker engine/image overrides, and locally available PDK-aware command-line tools. OpenLane 2.3.10 and its complete tool suite run from the pinned Docker image `ghcr.io/efabless/openlane2:2.3.10`. The environment uses Volare 0.19.2 and GF180MCU PDK release `c6d73a35f524070e85faff4a6a9eef49553ebc2b`.

## Reprovision the PDK

If the local PDK cache is missing, activate the environment and run:

```bash
source /home/kubew/g100-gf180-tools/env.sh
volare fetch --pdk-root "$VOLARE_HOME" --pdk gf180mcu c6d73a35f524070e85faff4a6a9eef49553ebc2b
mkdir -p "$PDK_ROOT/volare/gf180mcu"
ln -sfn "$VOLARE_HOME/volare/gf180mcu/versions" "$PDK_ROOT/volare/gf180mcu/versions"
volare enable --pdk-root "$PDK_ROOT" --pdk gf180mcu c6d73a35f524070e85faff4a6a9eef49553ebc2b
```

`PDK_ROOT` is a thin activation view and `VOLARE_HOME` is the Volare cache. Enabling the PDK creates its current-version pointer and variant links in the activation view, which points back to the cached version store. The enabled `gf180mcuD` variant contains OpenLane configurations for `gf180mcu_fd_sc_mcu7t5v0`, Magic technology files, and Netgen setup files. For OpenLane, mount both local PDK paths into the image at their identical absolute paths: the enabled PDK variant symlinks into the Volare store.

## Verify and run a reproducible flow

```bash
source /home/kubew/g100-gf180-tools/env.sh
volare output --pdk-root "$PDK_ROOT" --pdk gf180mcu
docker image inspect "$OPENLANE_IMAGE_OVERRIDE" --format '{{.Id}}'
docker run --rm "$OPENLANE_IMAGE_OVERRIDE" openlane --smoke-test

# Run the built-in 8-bit registered-adder GF180 smoke design.
./tools/test-gf180-run.sh
```

`tools/test-gf180-run.sh` bind-mounts the design, the enabled PDK root and Volare cache into the pinned OpenLane image at the same absolute paths. It uses a unique UTC run tag, writes the console log under `$GF180_ARTIFACT_ROOT/logs/`, and saves copied final views, PDK reports, all OpenLane step logs and `status.txt` under `$GF180_ARTIFACT_ROOT/<run-tag>/`. Defaults are `/home/kubew/g100-gf180-tools/artifacts`; each run is also retained in `/home/kubew/g100-gf180-tools/gf180-smoke/runs/<run-tag>`.

The runner accepts these optional environment variables:

- `GF180_RUN_TAG` — explicit unique run tag.
- `GF180_FLOW_ROOT`, `GF180_ENV_FILE` — isolated tool root or activation file.
- `GF180_DESIGN_DIR`, `GF180_CONFIG` — custom design directory and config.
- `GF180_ARTIFACT_ROOT` — destination for logs, reports and final views.
- `GF180_PDK_FAMILY`, `GF180_STD_CELL_LIBRARY` — process variant/library.
- `GF180_JOBS` — OpenLane worker count (default 2).
- `GF180_OPENLANE_ARGS` — extra OpenLane CLI arguments, such as floorplan overrides.

For the smoke design, the runner supplies `FP_SIZING=absolute`, `DIE_AREA=0,0,1000,1000`, and `FP_CORE_UTIL=25`. These small-die settings are only for the adder. For a real design, provide a validated config and override floorplan flags, for example:

```bash
GF180_DESIGN_DIR=/work/design \\
GF180_CONFIG=/work/design/config.json \\
GF180_ARTIFACT_ROOT=/work/gf180-artifacts \\
GF180_RUN_TAG=grx930_trial_001 \\
GF180_OPENLANE_ARGS='-c FP_SIZING=absolute -c DIE_AREA=0,0,3930,5120 -c FP_CORE_UTIL=30' \\
./tools/test-gf180-run.sh
```

The nested `--dockerized` OpenLane launcher is not used: inside this Docker-outside-of-Docker environment it resolves `/` as its working directory and asks Docker to bind-mount `/:/`, which the daemon rejects. Running the pinned image directly avoids that path issue.

The verified smoke run completed all 78 Classic-flow stages; antenna checks passed, Magic DRC reports zero errors, and Netgen reports a unique circuit match. GDS, netlist, LEF, ODB, and SDC are copied into the timestamped artifact directory. OpenLane 2.3.10 does not support KLayout DRC on GF180; Magic DRC is run instead.

Both the generic OpenLane smoke test and the minimal GF180 flow completed successfully. The PDK files resolve inside the pinned image when both local roots are mounted. Local Yosys, OpenROAD, Netgen, Magic, and Volare executables are resolvable; OpenLane itself runs from its pinned image.

## Scope and limitations

This smoke runner verifies the environment with an 8-bit adder; it does not claim the GRX930 RTL is a valid GF180 design or that the repository's separate OpenLane/legacy scripts are signoff-ready. A project PPA run must first confirm its RTL/config and use verified floorplan values. The legacy Makefile's `make pnr` and `make signoff` use separate Yosys/OpenROAD scripts and were not run.

The isolated assets are WSL-local and not committed. The PDK cache occupies about 4.8 GiB. The host has around 3.5 GiB available RAM, so larger placement and routing runs may need swap and may be slow.
