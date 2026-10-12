# Contributing

Start with [installation](docs/REPRODUCE.md) and
[design status](docs/PROJECT_STATUS.md). Keep a change small enough that its
source inputs, functional checks, and implementation effects can be reviewed.

## Python and documentation changes

Run from the checkout root:

```bash
python3 -m agent smoke
python3 -m unittest discover -s tests -v
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
```

Some tests use `tclsh`; install Tcl as described in the setup guide.
Add a regression test for a repaired failure. Offline tests must not require
an API key, an EDA license, a vendor installation, or a network connection.
Report any check you could not run.

## RTL and flow changes

1. Identify the baseline commit, edited files, design, and parameter set.
2. Keep reference RTL separate from modified sources. Preserve the source
   headers and third-party notices.
3. Check syntax/elaboration and run the relevant functional test before
   comparing PPA. A block check does not replace top-level integration testing.
4. State the tested operation, vectors, reset/handshake cases, and cycle counts.
   A test pass does not establish exhaustive equivalence or side-channel safety.
5. Compare baseline and edited designs with matching tools, libraries,
   constraints, implementation stages, and memory handling.
6. Save the exact commands and reports. Keep negative results and retractions.
   Follow the [result-reading guide](docs/RESULTS.md) and
   [recording standard](docs/DOCUMENTATION_STANDARD.md).

Do not check in API keys, license credentials, proprietary libraries, or PDK
files. Confirm redistribution rights before adding upstream RTL or test data.

## Add a design

Supply the upstream revision and license, complete RTL/file list, top module,
parameters/defines, clocks and reset conventions, memory/ROM inputs, a
self-checking functional test, and a reproducible baseline run. Document missing
parts in [project status](docs/PROJECT_STATUS.md). A manifest template alone
must not be described as design support or a measured result.

## Before publishing a release

- Test setup in a fresh environment and run every offline check above.
- Check that all current documentation links resolve.
- List which hardware flows were actually rerun, which only passed preparation,
  and which are blocked.
- Confirm each published metric has an available source report and matching
  baseline configuration.
- Complete the [release and license review](docs/RELEASE_CHECKLIST.md).
  Historical vendor snapshots and logs are not cleared for redistribution.
- Verify that no secrets, restricted libraries, or local account details were
  added to the release.

A release or paper should cite the exact commit. Do not replace the historical
run descriptions with claims about the newest checkout without rerunning them.
