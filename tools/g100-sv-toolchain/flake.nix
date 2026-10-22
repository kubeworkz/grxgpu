{
  description = "Pinned Yosys 0.46, Synlig and Surelog frontend for Vortex elaboration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/9b696460ac78b5ccfc17c854d8c976f20456e943";
    yosys-src = {
      url = "git+https://github.com/YosysHQ/yosys.git?rev=e97731b9dda91fa5fa53ed87df7c34163ba59a41&submodules=1";
      flake = false;
    };
    synlig-src = {
      url = "git+https://github.com/chipsalliance/synlig.git?rev=fd4b2bd9510c02c4cf42f8c4c6468c5c0a7dd9e6";
      flake = false;
    };
    surelog-src = {
      url = "git+https://github.com/chipsalliance/Surelog.git?rev=37ce1bbf98ca26ba2e18603a271b55ac05e121d5&submodules=1";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, yosys-src, synlig-src, surelog-src }:
    let
      systems = [ "x86_64-linux" ];
      eachSystem = nixpkgs.lib.genAttrs systems;
    in {
      packages = eachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
          surelog = pkgs.stdenv.mkDerivation {
            pname = "surelog";
            version = "1.82-37ce1bb";
            src = surelog-src;
            nativeBuildInputs = with pkgs; [ cmake ninja pkg-config python3 jdk ];
            buildInputs = with pkgs; [ antlr4 capnproto gtest nlohmann_json gperftools antlr4.runtime.cpp ];
            cmakeFlags = [
              "-DCMAKE_BUILD_TYPE=Release"
              "-DCMAKE_POSITION_INDEPENDENT_CODE=ON"
              "-DSURELOG_BUILD_TESTS=OFF"
              "-DSURELOG_USE_HOST_CAPNP=ON"
              "-DSURELOG_USE_HOST_GTEST=ON"
              "-DSURELOG_USE_HOST_ANTLR=ON"
              "-DSURELOG_USE_HOST_JSON=ON"
            ];
            doCheck = false;
          };

          yosys = pkgs.stdenv.mkDerivation {
            pname = "yosys";
            version = "0.46-e97731b";
            src = yosys-src;
            nativeBuildInputs = with pkgs; [ bison flex gnumake pkg-config python3 tcl ];
            buildInputs = with pkgs; [ boost readline libffi zlib ];
            makeFlags = [ "PREFIX=$(out)" "ENABLE_READLINE=0" "ENABLE_EDITLINE=1" ];
            enableParallelBuilding = true;
            doCheck = false;
          };

          synlig = pkgs.stdenv.mkDerivation {
            pname = "synlig";
            version = "fd4b2bd";
            src = synlig-src;
            nativeBuildInputs = with pkgs; [ cmake gnumake pkg-config ];
            buildInputs = [ yosys surelog pkgs.capnproto pkgs.antlr4 pkgs.antlr4.runtime.cpp ];
            postPatch = ''
              rm -rf third_party/yosys third_party/surelog
              mkdir -p third_party/yosys third_party/surelog
              cp -a ${yosys-src}/. third_party/yosys/
              cp -a ${surelog-src}/. third_party/surelog/
              rm -f third_party/Build.surelog.mk
              cp ${pkgs.writeText "Build.yosys.mk" ''
                t := yosys
                ts := $(call GetTargetStructName,$(t))
                $(ts).src_dir := $(shell yosys-config --datdir/include)
                $(ts).mod_dir := $(TOP_DIR)third_party/yosys_mod/
              ''} third_party/Build.yosys.mk
            '';
            buildPhase = ''
              runHook preBuild
              make build@systemverilog-plugin -j$NIX_BUILD_CORES LDFLAGS="$(yosys-config --ldflags)"
              runHook postBuild
            '';
            installPhase = ''
              mkdir -p "$out/share/yosys/plugins"
              install -m 0555 build/release/systemverilog-plugin/systemverilog.so "$out/share/yosys/plugins/synlig-sv.so"
            '';
          };

          toolchain = pkgs.symlinkJoin {
            name = "vortex-sv-toolchain";
            paths = [ yosys surelog synlig ];
            postBuild = ''
              mkdir -p "$out/bin"
              rm -f "$out/bin/yosys"
              cp ${yosys}/bin/yosys "$out/bin/yosys"
              rm -f "$out/bin/yosys-abc"
              cp ${yosys}/bin/yosys-abc "$out/bin/yosys-abc"
              ln -sf ${surelog}/bin/surelog "$out/bin/surelog"
              ln -sf ${synlig}/share/yosys/plugins/synlig-sv.so "$out/share/yosys/plugins/synlig-sv.so"
            '';
          };
        in {
          default = toolchain;
          inherit yosys surelog synlig;
        });

      checks = eachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
          toolchain = self.packages.${system}.default;
        in {
          default = pkgs.runCommand "g100-sv-toolchain-lowmem-smoke" {
            nativeBuildInputs = [ pkgs.gnugrep ];
          } ''
            set -eu
            test ! -L ${toolchain}/bin/yosys
            test ! -L ${toolchain}/bin/yosys-abc
            test -x ${toolchain}/bin/surelog
            mkdir work
            cd work
            cat > tiny.sv <<'SV'
            module tiny(input logic a, output logic y);
              assign y = a;
            endmodule
            SV
            cat > smoke.ys <<YS
            read_systemverilog -lowmem -mt 1 -mp 1 -noinfo -top tiny "$PWD/tiny.sv"
            YS
            ${toolchain}/bin/yosys \
              -m ${toolchain}/share/yosys/plugins/synlig-sv.so \
              -Q -s smoke.ys -l smoke.log > run.log 2>&1
            grep -F "${toolchain}/bin/surelog" run.log
            grep -F "Surelog preproc status: 0" run.log
            grep -F "Surelog parsing status: 0" run.log
            grep -F "[  FATAL] : 0" run.log
            grep -F "[ SYNTAX] : 0" run.log
            grep -F "[  ERROR] : 0" run.log
            grep -F "[WARNING] : 0" run.log
            touch "$out"
          '';
        });

      devShells = eachSystem (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = [ self.packages.${system}.default pkgs.coreutils pkgs.python3 ];
            shellHook = ''
              export YOSYS="$PWD/result/bin/yosys"
              export SYNLIG_PLUGIN="$PWD/result/share/yosys/plugins/synlig-sv.so"
            '';
          };
        });
    };
}
