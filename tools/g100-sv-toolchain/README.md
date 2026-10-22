# Pinned SystemVerilog frontend toolchain

This flake keeps the observed source revisions explicit: Yosys 0.46 (`e97731b9dda91fa5fa53ed87df7c34163ba59a41`), Synlig (`fd4b2bd9510c02c4cf42f8c4c6468c5c0a7dd9e6`), and Surelog (`37ce1bbf98ca26ba2e18603a271b55ac05e121d5`). Its Nixpkgs input is explicitly locked to `9b696460ac78b5ccfc17c854d8c976f20456e943`; this is a new reproducible pin, not a recovered historical pin for the WSL environment.

Build on Linux using the included lock file:

```sh
cd tools/g100-sv-toolchain
nix --extra-experimental-features 'nix-command flakes' build --no-link --print-out-paths
```

If you intentionally change an input revision, regenerate and review `flake.lock` with `nix --extra-experimental-features 'nix-command flakes' flake lock`.

The lock file fixes the fetched Git revisions, source hashes, and Nixpkgs. `--submodules=1` is used for Yosys (ABC) and Surelog. Synlig's source revision records different Yosys/Surelog submodule commits; the derivation explicitly replaces those checkouts with the top-level pinned source inputs before building its systemverilog plugin. The build uses separate pinned Yosys and Surelog derivations and then the Synlig plugin built against them.

The toolchain package installs a real copy of the pinned Yosys executable beside a `surelog` symlink. Surelog's embedded plugin derives its companion path from `/proc/self/exe`, so a Yosys symlink in the Nix store would still resolve beside the original Yosys and fail to find Surelog. Yosys' compiled-in data directory and ABC paths remain Nix-store-absolute, so `YOSYS_PREFIX` is not needed. The package also places the `yosys-abc` companion beside the copy because Yosys itself resolves ABC from `/proc/self/exe`. Do not replace these executable copies with wrappers or symlinks.

Run the focused low-memory smoke test and the Nix checks with:

```sh
nix --extra-experimental-features 'nix-command flakes' build .#checks.x86_64-linux.default
nix --extra-experimental-features 'nix-command flakes' flake check
```

The smoke check launches the packaged Yosys and Synlig plugin on a tiny SystemVerilog module with `-lowmem -mt 1 -mp 1`. It verifies that both Surelog subprocesses run from the packaged `bin/surelog` path and that Surelog reports zero fatal, syntax, and error diagnostics. A passing smoke test validates the companion-executable layout only; it does not prove full Vortex elaboration or synthesis.

If intentionally changing an input revision, regenerate and review `flake.lock` with `nix --extra-experimental-features 'nix-command flakes' flake lock`; do not advance source commits to work around build failures. Verify tool versions and plugin registration against the pins. This Nix flake has not yet been built in this workspace, so the pinned cross-version trio and the new check still need a Nix build before this flow is considered verified.
