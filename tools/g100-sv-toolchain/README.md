# Pinned SystemVerilog frontend toolchain

This flake keeps the observed source revisions explicit: Yosys 0.46 (`e97731b9dda91fa5fa53ed87df7c34163ba59a41`), Synlig (`fd4b2bd9510c02c4cf42f8c4c6468c5c0a7dd9e6`), and Surelog (`37ce1bbf98ca26ba2e18603a271b55ac05e121d5`). Its Nixpkgs input is explicitly locked to `9b696460ac78b5ccfc17c854d8c976f20456e943`; this is a new reproducible pin, not a recovered historical pin for the WSL environment.

Build on Linux using the included lock file:

```sh
cd tools/g100-sv-toolchain
nix --extra-experimental-features 'nix-command flakes' build --no-link --print-out-paths
```

If you intentionally change an input revision, regenerate and review `flake.lock` with `nix --extra-experimental-features 'nix-command flakes' flake lock`.

The lock file fixes the fetched Git revisions, source hashes, and Nixpkgs. `--submodules=1` is used for Yosys (ABC) and Surelog. Synlig's source revision records different Yosys/Surelog submodule commits; the derivation explicitly replaces those checkouts with the top-level pinned source inputs before building its systemverilog plugin. The build uses separate pinned Yosys and Surelog derivations and then the Synlig plugin built against them.

This flake has not yet been built in the interrupted session. It is a reproducibility starting point, not proof that this cross-version trio compiles. Resolve any Nix expression/build errors with the pinned revisions; do not silently advance a source commit. Verify after build that `yosys -V`, `surelog`'s version banner, and `read_systemverilog` plugin registration match the pins. Pin any dependency/build fixes in this flake and regenerate `flake.lock` only for intentional changes.
