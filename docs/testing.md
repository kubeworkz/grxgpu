# Testing

## Running a Vortex application

The framework provides a utility script: blackbox.sh under the /ci/ folder for executing applications in the tests tree. It gets copied into the `build` directory with all the environment variables resolved, so you should run it from the `build` directory as follows:
You can query the commandline options of the tool using:

    $ ./ci/blackbox.sh --help

To execute sgemm test program on the simx driver and passing "-n10" as argument to sgemm:

    $ ./ci/blackbox.sh --driver=simx --app=sgemm --args="-n10"

You can execute the same application of a GPU architecture with 2 cores:

    $ ./ci/blackbox.sh --core=2 --driver=simx --app=sgemm --args="-n10"

When excuting, Blackbox needs to recompile the driver if the desired architecture changes.
It tracks the latest configuration in a file under the current directory blackbox.<driver>.cache.
To avoid having to rebuild the driver all the time, Blackbox checks if the latest cached configuration matches the current.

## Building the Verilator Drivers

The Verilator-based builds — `rtlsim`, `opaesim`, `xrtsim`, and each block test
under `hw/unittest/` — run in two separate steps:

1. **Verilate.** Verilator parses the RTL and writes the C++ model, plus its own
   makefile `V<top>.mk`, into an object directory: `rtlsim.obj_dir` and
   `librtlsim.so.obj_dir` for rtlsim, `libopae-c-sim.so.obj_dir` and
   `libxrtsim.so.obj_dir` for the FPGA shims, and `obj_dir` for a block test.
2. **Compile and link.** make runs that generated makefile inside the object
   directory to compile the model and link the driver or simulator library.

`make` runs both steps. To run only the first, which is the expensive one, use
the `verilate` target:

    $ make -C sim/rtlsim verilate
    $ make -C sim/opaesim verilate
    $ make -C hw/unittest/generic_queue verilate

This prepares a model once per configuration, so a later build or a test loop
does not pay for verilation again. `verilate` never compiles or links.

### Resuming an Interrupted Build

The two steps are deliberately kept apart so that a build that is killed
resumes where it stopped. Do not invoke `verilator --build` by hand: it
re-verilates on every run and drops the objects of the previous one.

- Verilation is skipped while `V<top>.mk` is newer than the inputs it was
  generated from: the RTL, the host sources, and, for the sim drivers, the
  flag stamp.
- Compilation is driven by make inside the object directory, so only
  translation units that are missing or older than their sources are rebuilt.
- The link is redone from those objects on every build, and the artifact is
  deleted first, so a binary truncated by a killed link is never kept.

Re-run the same command after an interruption and it continues from the
surviving objects. `blackbox.sh` builds its drivers through the same targets
(the runtime Makefiles under `sw/runtime/` call into `sim/`), so an interrupted
blackbox run resumes the same way.

### Forcing a Rebuild

Prefer changing the request over deleting files:

- For `rtlsim`, `opaesim`, and `xrtsim`, a changed flag set updates the
  configuration stamp (`rtlsim_config.stamp` and friends), which discards the
  object directory before re-verilating. The stamp is compared by content, so
  passing the same flags again does not trigger a rebuild.
- Block tests under `hw/unittest/` have no flag stamp; run `make clean` there
  before changing `CONFIGS` or `PARAMS`.
- Deleting only the linked artifact does not recompile anything: the objects
  are current, so the next build just links them again.

`THREADS=<n>` caps the parallelism of both steps, which matters on machines
with many cores but little RAM (see [simulation.md](simulation.md)).

## Running Benchmarks

The Vortex test suite is located under the /test/ folder
You can execute the default regression suite by running the following commands at the root folder.

    $ make -C tests/regression run-simx
    $ make -C tests/regression run-rtlsim

You can also run regression applications in parallel from a configured build tree.
The script accepts `simx`, `rtlsim`, or `rtl` (alias for `rtlsim`) and writes
per-test logs plus a summary under `tests/regression/logs/`.

    $ ./tests/regression/run_parallel.sh simx -j 8
    $ ./tests/regression/run_parallel.sh rtl -j 2

By default it scans every first-level regression directory with a Makefile. Use
`--suite makefile` to run the same test list selected by `tests/regression/Makefile`.

You can execute the default opncl suite by running the following commands at the root folder.

    $ make -C tests/opencl run-simx
    $ make -C tests/opencl run-rtlsim

## Creating Your Own Regression Test

Inside `tests/regression` you will find a series of folders which are named based on what they test.
You can view the tests to see which ones have tests similar to what you are trying to create new tests for.
Once you have found a similar baseline, you can copy the folder and rename it to what you are planning to test.
A regression test typically implements the following files:
- ***kernel.cpp*** contains the GPU kernel code.
- ***main.cpp*** contains the host CPU code.
- ***Makefile*** defines the compiler build commands for the CPU and GPU binaries.

Sync your build folder: `$ ../configure`

Compile your test: `$ make -C tests/regression/<test-name>`

Run your test: `$ ./ci/blackbox.sh --driver=simx --app=<test-name> --debug`

## Adding Your Tests to the CI Pipeline
If you are a contributor, then you will need to add tests that integrate into the continuous integration pipeline. Remember, Pull Requests cannot be merged unless new code has tests and existing tests do not regress. Furthermore, if you are contributing a new feature, it is recommended that you add the ability to enable / disable the new feature that you are adding. See more at [CONTRIBUTING.md](../CONTRIBUTING.md) and [continuous_integration.md](continuous_integration.md).