# Reproducing These Results: A Step-by-Step Playbook

This guide takes you from a fresh machine to reproducing the three things this
project claims:

1. **Correctness**, the optimized RTL still computes HQC correctly (the
   Known-Answer Test passes at all three security levels).
2. **The timing wins**, re-synthesizing reproduces the worst-slack numbers in
   [01_results.md](01_results.md).
3. **The agent**, the LLM-driven optimizer runs a full flight end to end.

It is written for someone who has not used this codebase before. Commands are
meant to be copy-pasted one at a time; read the expected output before moving on.

---

## 0. What you need

You need three things: a Linux environment, Xilinx Vivado, and Python 3.

**If you are on Linux already:** you can ignore every mention of WSL below and
run the commands directly in your terminal.

**If you are on Windows:** Vivado's Linux edition is the one this project uses,
and it runs inside WSL2 (Windows Subsystem for Linux). You install WSL once, then
work entirely inside the Ubuntu terminal it gives you. Everything after the WSL
setup is identical to a native-Linux user's steps.

### 0a. (Windows only) Install WSL2 + Ubuntu

In an Administrator PowerShell:

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted, then launch "Ubuntu" from the Start menu and create a Linux
username/password when asked. From here on, every command in this guide runs in
that Ubuntu terminal, not in PowerShell. Your Windows `C:` drive is visible
inside WSL at `/mnt/c/`.

### 0b. Install Vivado 2025.2 (Linux edition) and the required compatibility steps

Install the Vivado 2025.2 Linux edition (the free edition is sufficient for this
device). This project targets the Artix-7 `xc7a200tfbg676-1`. The exact
environment this project was developed and verified on is: Windows 11 with WSL2
Ubuntu 24.04, Vivado 2025.2 installed inside WSL at `/tools/Xilinx/2025.2`.

The following one-time setup steps are required beyond a default install. These
are not optional; Vivado 2025.2 will not run correctly on Ubuntu 24 without them.

**1. Python compatibility.** Several scripts call `python`:

```bash
sudo apt install -y python-is-python3
```

**2. ncurses and tinfo compatibility.** Vivado needs `libncurses.so.5` and
`libtinfo.so.5`, but Ubuntu 24 only ships the `.so.6` versions. Install the
libraries and create the symlinks:

```bash
sudo apt install -y libncurses6 libtinfo6
sudo ln -s /usr/lib/x86_64-linux-gnu/libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5
sudo ln -s /usr/lib/x86_64-linux-gnu/libtinfo.so.6  /usr/lib/x86_64-linux-gnu/libtinfo.so.5
```

(If Vivado launches with a `libncurses.so.5` error, this is the fix.)

**3. Locale.** Vivado expects `en_US.UTF-8`:

```bash
sudo dpkg-reconfigure locales
# select en_US.UTF-8 UTF-8 and set it as the default
```

**4. Vivado's own library installer.** Run it once after installing Vivado:

```bash
sudo /tools/Xilinx/2025.2/Vivado/scripts/installLibs.sh
```

**5. Put Vivado on your PATH.** Every new terminal session needs this, so add it
to your `~/.bashrc` (adjust the path to match your install location):

```bash
source /tools/Xilinx/2025.2/Vivado/settings64.sh
vivado -version    # should print Vivado v.2025.2
```

The scripts in this repo invoke Vivado as the bare command `vivado`, so once
`vivado -version` works in a fresh shell, the scripts will find it.

### 0c. Python 3

```bash
python3 --version    # 3.10+ is fine
```

No third-party Python packages are required for the correctness and timing steps
(Sections 2 and 3). The agent step (Section 4) needs one package, `anthropic`,
covered there.

---

## 1. Get the code

```bash
cd ~                      # or wherever you keep projects; on Windows /mnt/c/... works too
git clone https://github.com/hsc-research/LLM-Aided-PQC.git
cd LLM-Aided-PQC
```

Orientation, the directories you will touch:

- `build/keygen/`, `build/encap/`, `build/decap/`: the three elaborated RTL
  build trees. These are what gets synthesized and simulated. (HQC's three
  operations; each is built and tested independently.)
- `agent/`, the optimization agent and its tooling. The entry points you will
  run are `kat_gate.py`, `path_extractor.py`, and `loop_v21.py`.
- `synth_out/`, synthesis outputs land here. The `paths/*_top20.rpt` files are
  the per-board critical-path reports; `full_matrix.json` is the cross-level
  summary.
- `docs/`, this documentation.

---

## 2. Prove correctness: the Known-Answer Test (KAT)

This is the single most important check. It runs the full HQC chain , 
key generation, encapsulation, decapsulation, in simulation and verifies that
the shared secret recovered at the end matches end to end, at all three security
levels. This is a cryptographic correctness check: much stronger than a unit
testbench, though note it is an end-to-end self-consistency check, not a
comparison against the official NIST HQC response vectors. If it passes, the RTL
is functionally correct in the sense that every optimization preserves the
key-encapsulation behavior.

```bash
python3 agent/kat_gate.py
```

Expected output (the simulations take a few minutes total):

```
KAT GATE: running full keygen -> encap -> decap verification
=======================================================
  ...
=======================================================
KAT RESULT: PASS
  HQC-128: MATCH
  HQC-192: MATCH
  HQC-256: MATCH
```

`PASS` with three `MATCH` lines means every optimization in this repo preserves
correctness. This has been verified from a clean clone: cloning the repository
fresh and running this command reaches `PASS` at all three levels with no extra
setup beyond Section 0. If you see `FAIL` or a mismatch, something in your build
tree differs from the committed RTL, re-clone and confirm you have not locally
edited the `build/` trees.

> If a run errors with a Vivado "project already exists" message, remove the
> leftover simulation project directories and re-run:
> `rm -rf test_keygen test_encap test_decap`

---

## 3. Prove the timing wins: re-synthesize and read the slack

Each board is synthesized out-of-context at the 200 MHz (5.000 ns) constraint,
and the worst negative slack (WNS) is read from the top of the timing report.
The tool that does this in one step is `path_extractor.py`:

```bash
python3 agent/path_extractor.py keygen hqc192 20
```

This synthesizes `keygen` at HQC-192 and prints the top 20 critical paths. The
**worst slack** is the first number in the table; compare it to the value in the
table in [01_results.md](01_results.md).

### Reproduce a specific result

Pick the operation and level you want to confirm, run the command, then compare
the worst slack against the cross-level table in [01_results.md](01_results.md),
which is the single source of truth for the expected numbers:

| To confirm... | Run |
|---------------|-----|
| keygen near closure (any level) | `python3 agent/path_extractor.py keygen hqc192 20` (or `hqc128` / `hqc256`) |
| encap improvement (any level) | `python3 agent/path_extractor.py encap hqc256 20` (or `hqc128` / `hqc192`) |
| decap (the placement-bound case) | `python3 agent/path_extractor.py decap hqc128 20` |

The worst slack is the first number in the printed table. It should match the
corresponding cell in `01_results.md` to within a few thousandths of a ns.

Small variation (a few thousandths of a ns) between runs is normal: placement and
routing have run-to-run variance. The cluster *structure* (which registers source
the worst paths) is the stable, reproducible part, not the third decimal place.

### The whole table at once

To regenerate the full 3-operation by 3-level matrix into
`synth_out/full_matrix.json`:

```bash
python3 - << 'PY'
import sys; sys.path.insert(0, 'agent')
from synthesizer import run_synthesis
import json
results = []
for m in ['keygen', 'encap', 'decap']:
    for lv in ['hqc128', 'hqc192', 'hqc256']:
        r = run_synthesis(m, lv)
        results.append(r); print(json.dumps(r), flush=True)
open('synth_out/full_matrix.json', 'w').write(json.dumps(results, indent=2))
print('MATRIX COMPLETE')
PY
```

The decap runs are the long ones; the full matrix takes a while. Each line printed
includes `wns_ns` and `fmax_mhz`.

---

## 4. Run the agent end to end

The agent automates the optimization loop: it picks a critical-path cluster,
asks a language model to propose an equivalence-preserving edit, applies that edit
only through a set of safety checks, re-synthesizes, measures the gain, and runs
the KAT, reverting anything that does not improve timing or that breaks
correctness.

### 4a. Provide an LLM API key

The proposal step calls a large language model. The repo was developed against
one commercial LLM API, but the design is vendor-neutral: the model only ever
returns a structured list of typed edit operations, which the local harness then
verifies and applies. See Section 5 for how to point it at a different provider.

As written, the proposal step uses the Anthropic Python client, which needs the
package installed and a key in the standard environment variable:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
```

(`anthropic.Anthropic()` in `agent/optimizer_v2.py` reads `ANTHROPIC_API_KEY`
automatically.) To use a different provider instead, see Section 5, you replace
one function and this key/package step changes accordingly.

### 4b. Run a flight

```bash
python3 agent/loop_v21.py keygen hqc192
```

A "flight" proceeds through these stages, all printed as it goes:

1. **Target selection**, the code picks one critical-path cluster and prints it.
2. **Proposal**, the model returns either `no_action` (with a reason) or an
   experiment (a list of typed edits) as JSON.
3. **Dry-run echo**, the harness shows the exact diff the edits would produce and
   the model confirms it.
4. **Gated apply**, the edits are applied only if every safety check passes.
5. **Synthesis + gain**, the board is re-synthesized; the per-cluster slack
   change is printed.
6. **KAT**, if the gain clears the threshold, the full correctness chain runs.

A successful flight ends with a `VERIFIED` message and leaves the change staged
for you to review and commit. A flight that finds nothing worthwhile ends with a
reasoned `no_action` or an auto-reverted result, that is the agent working
correctly, not failing. Each flight appends one line to `agent/flight_log.jsonl`.

> The agent never commits for you. Review the diff and run `git commit` yourself.

---

## 5. Using an AI effectively in this workflow

This section is the practical guidance the project wishes it had had at the start.

### What the AI does, and what it does not

The language model's *only* job is the creative step a human would otherwise do
by hand: look at a critical-path cluster and propose an edit that removes the
bottleneck while preserving behavior. It does **not** write trusted RTL. It
returns a structured proposal; the harness (`agent/edit_ops.py`) re-derives every
count, checks every safety property, and refuses anything that does not hold. The
correctness guarantee comes from the KAT and the gates, never from trusting the
model's output.

This is the central lesson: **let the AI propose, let deterministic code verify.**
Every early failure in this project came from giving the model a decision that
code should have owned (which file, how many sites, where to place a
declaration). The architecture in [04_agent_architecture.md](04_agent_architecture.md)
exists to take those decisions away from the model.

### Pointing it at a different LLM

The model call is isolated in `agent/optimizer_v2.py`. To use a different
provider, replace the single function that sends the prompt and returns text;
keep the prompt and the JSON contract the same. The prompt itself, which encodes
the optimization taxonomy and the edit-operation grammar, is the valuable,
reusable part and is provider-independent. Read it before swapping anything; it is
the distilled methodology.

### Driving it toward a specific outcome

- **To attack a specific board:** `python3 agent/loop_v21.py <module> <level>`.
  The selector picks the worst un-exhausted cluster on that board.
- **To re-attempt a cluster you previously skip-listed:** delete
  `agent/skiplist.json` (it is regenerated each run) and re-fly.
- **To understand why the agent declined:** read its `no_action` reason and the
  `agent/flight_log.jsonl` entry. A decline usually means the cluster is
  placement-bound (see the fingerprints in
  [02_optimization_taxonomy.md](02_optimization_taxonomy.md)), which RTL edits
  cannot fix.

### Using AI to read the results yourself

When you run `path_extractor.py` and get a wall of critical paths, that output is
exactly what the agent's prompt consumes. You can paste a board into any capable
LLM along with [02_optimization_taxonomy.md](02_optimization_taxonomy.md) and ask
it to classify the worst cluster, it is a fast way to learn the fingerprints
before trusting the automated loop.

---

## 6. Troubleshooting (real issues from this project)

- **Vivado not found:** you did not source `settings64.sh` in this shell. See 0b.
- **`libncurses.so.5` error on launch:** create the symlink in 0b (and the
  matching `libtinfo.so.5` symlink).
- **KAT "project already exists":** `rm -rf test_keygen test_encap test_decap`,
  then re-run.
- **A clock-related synthesis error:** the clock port in these modules is named
  `clk` (not `clk_i`), and the constraint must be created after `synth_design` in
  the direct OOC flow. The provided scripts already handle this; the note matters
  only if you write your own flow.
- **Slack differs in the third decimal from the table:** expected run-to-run
  placement variance. Confirm the cluster structure matches, not the exact ns.
- **The agent proposes something that gets refused:** that is a gate doing its
  job. Read the refusal message; it names the property that failed.

---

## 7. Manual simulation and deeper gotchas

The KAT gate in Section 2 wraps the simulation flow, so most users never need
the steps below. They are recorded here because they cost real debugging time and
will matter if you run the simulations by hand or modify the build flow.

### The Makefile `mkdir` dependency bug

The Makefile's `run_xilinx_sim_keygen` target depends on `build_keygen`, which
uses a bare `mkdir` that fails if the directory already exists. The workaround is
to run the build once, then call Vivado directly for reruns:

```bash
PK=$(openssl rand -hex 40)
SK=$(openssl rand -hex 40)
make build_keygen pk_seed=$PK sk_seed=$SK

# To rerun later, first clean:
make clean
# Then run the sim without re-triggering build_keygen:
mkdir -p ./build/keygen/output
vivado -mode batch -nojournal -nolog -notrace -source ./build/keygen/tb/keygen.tcl
```

### The two versions of `seed_align.py`

keygen and joint_design use different versions of `seed_align.py`:

- `hardware/keygen/memory_files/seed_align.py` takes 2 arguments (seed, filename).
- `hardware/encap/memory_files/seed_align.py` takes 4 arguments (seed, bytes,
  filename, endianness).

The Makefile is already correct for both. Do not add the extra arguments to the
keygen call: the keygen script ignores them and will write its output to a file
literally named `40`.

### Where the output lands

After a keygen simulation, output files appear in:

```
test_keygen/test_keygen.sim/sim_1/behav/xsim/
```

including `S_output_*.out`, `X_output_*.out`, `Y_output_*.out`,
`vect_set_rand_output_*.out`, and the binary memory dumps `h_*.in`, `s_*.in`,
`x_*.in`, `y_*.in` that feed encapsulation and decapsulation.

### Seed reproducibility

The keygen seeds are generated randomly by `openssl rand -hex 40`, so they are
unique per run. Anyone using the same seeds with the same RTL gets identical
output, which is the deterministic property of HQC, useful for reproducing a
specific run or comparing outputs against a reference software implementation.

---

# Part II: ML-DSA

Sections 0-7 above cover HQC, the first case study. The remaining sections
cover ML-DSA (GMU/Beckwith codebase), the second scheme. The environment setup
in Section 0 and the general AI-workflow guidance in Section 5 apply to both;
everything below is ML-DSA specific.

## 8. ML-DSA: Prove correctness (full KAT gate)

ML-DSA correctness is verified against its own source tree, separate from HQC:

```
ROOT   = /mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main
SRC    = ROOT/ref_combined/src
TB     = ROOT/ref_combined/src_tb/tb_keygen_top.v
COMMON = ROOT/common
KAT    = ROOT/KAT
```

The gate runs the ENTIRE keygen pipeline (~50 files, mixed Verilog/VHDL
including Keccak) via Vivado xsim against NIST KAT vectors: 25 vectors x 3
security levels (75 total). This is the outer, full-design gate, distinct from
the per-block lockstep gates, which only verify fixed-latency equivalence and
can miss a block that shifts by a cycle.

Usage:

```bash
python3 agent/mldsa/full_kat_gate.py [override_dir] [--vectors N] [--timeout S]
```

- No arg: pristine baseline.
- `override_dir` (e.g. `agent/mldsa/mldsa_src`): same-named files there override
  the pristine SRC files by basename.
- `--vectors N`: run a subset of N KAT vectors instead of all 75.
- `--timeout S`: override the default 24h timeout.

Pristine baseline:

```bash
python3 agent/mldsa/full_kat_gate.py
```

Against tracked/optimized sources:

```bash
python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src
```

PASS criterion: `testbench done` printed and zero `WRONG` lines. Batch mode (the
default) completes a full 75-KAT pristine run in about 1m37s wall, cheap enough
to run on every candidate edit, not just pre-commit.

Logs: `agent/mldsa/fullkat_run.log`. Parsed per-vector results:
`agent/mldsa/fullkat_vectors.json`.

If interrupted or failed, the script preserves the temp work directory and
prints its path (`workdir preserved: /tmp/mldsa_fullkat_FAILED_...`).

Do not edit the pristine SRC tree directly. A `.bak` file appearing next to a
pristine source is a contamination signal, meaning an edit was accidentally
applied to pristine instead of routed through `agent/mldsa/mldsa_src`. Periodic
check: `ls SRC/*.bak` should be empty.

---

## 9. ML-DSA: Prove the block-level timing wins

Block-level timing reproduction reuses `agent/path_extractor.py` and
`agent/synthesizer.py`, with the param_set argument set to `mldsa`:

```bash
python3 agent/path_extractor.py <module> mldsa 20
```

Valid `<module>` names (from `MODULE_SOURCES` in `agent/synthesizer.py`):

`butterfly`, `expandmask_ext`, `gen_a_ext`, `rejection_a`, `decomposer_unit`,
`coeff_decomposer`, `rejection_y`, `rejection_s`, `makehint`, `gen_c`,
`decoder`, `usehint`, `sampler_s_pristine` / `sampler_s_opt`,
`sampler_y_pristine` / `sampler_y_opt`, `sampler_a_pristine` / `sampler_a_opt`,
`encoder`, `combined_top`.

Example:

```bash
python3 agent/path_extractor.py decoder mldsa 20
```

The `*_pristine` / `*_opt` pairs share the same wrapper source and swap only the
inner block, letting you diff timing directly between pristine and optimized
versions of that block in composition.

Composition is not guaranteed to inherit block-level wins. Documented case:
`rejection_a`'s `max_fanout` attribute win (+0.076 ns in isolation) INVERTED to
a loss in the `sampler_a` wrapper (-0.446 ns) once placed in context, and was
later reverted to pristine for that reason. Structural rewrites
(flag-precompute, constant-LUT collapse, sign-select) transferred cleanly in all
measured cases; attribute-only edits (max_fanout and similar) did not, and must
be re-validated at the composition level before being kept.

---

## 10. ML-DSA: Full-chip integration and the post-route acceptance rule

Post-synthesis (OOC) chip-level estimates are NOT the accept/reject standard for
ML-DSA at the chip level; post-route is. Post-synthesis chip comparisons showed
the optimized `combined_top` marginally worse than pristine (a real,
deterministic -0.217 ns to -0.244 ns regression, confirmed non-noise by a 3-run
variability check). Post-route with `phys_opt` reverses this: the optimized
design wins at every measured corner.

| Corner | Pristine WNS / fmax | Optimized WNS / fmax | delta |
|---|---|---|---|
| -1 grade, 5.00 ns (200 MHz stretch) | -10.318 / 65.3 MHz | -8.766 / 72.6 MHz | +11.2% |
| -1 grade, 8.60 ns | -5.995 / 68.5 MHz | -5.017 / 73.4 MHz | +7.2% |
| -3 grade, 8.62 ns (116 MHz GMU-comparable) | -1.974 / 94.4 MHz | -1.779 / 96.2 MHz | +1.9% |

Post-route (implementation) is run via `agent/impl_runner.py`:

```bash
python3 agent/impl_runner.py <module> [period] [--pristine]
```

- `<module>`: e.g. `combined_top`.
- `[period]`: target clock period in ns. Defaults to 8.6 if omitted.
- `--pristine`: runs the pristine variant instead of the tracked/optimized one
  (internally maps to a `<module>_pristine` key in `MODULE_SOURCES`).

Note: this script does not expose the -1 vs -3 speed grade as a command-line
argument. The part/grade used for a given corner is set elsewhere in the
project's Vivado configuration, not passed here. Confirm the active part/grade
before comparing against the table above.

Commands matching the table's three corners (optimized shown; add `--pristine`
for the pristine row):

```bash
python3 agent/impl_runner.py combined_top 5.00
python3 agent/impl_runner.py combined_top 5.00 --pristine
python3 agent/impl_runner.py combined_top 8.60
python3 agent/impl_runner.py combined_top 8.60 --pristine
python3 agent/impl_runner.py combined_top 8.62
python3 agent/impl_runner.py combined_top 8.62 --pristine
```

`combined_top` is registered in `agent/synthesizer.py` (~39 Verilog + 11 VHDL
files, Keccak included via VHDL) with two variants: pristine (all GMU original
sources) and the tracked-override version (every committed block win applied by
basename).

WSL memory note: full-chip synthesis OOM-killed at the default 7.6 GB WSL memory
allocation. It was raised to 12 GB to complete. Each full-chip run took roughly
15-40 minutes observed at 12 GB.

Chip-level critical path: both pristine and optimized bind on the DECODER to
ENCODER cone, specifically `encoder.v`'s PISO output merge (a 256-bit
variable-length shift register), not any single arithmetic block. This is
consistent with GMU's own paper (Beckwith et al., ePrint 2021/1451), which
states their critical path is within the interconnect for the shared Keccak
modules. Chip-level absolute timing closure is explicitly NOT claimed by this
project: block-level wins are real and KAT-verified in isolation, but the
chip-level bottleneck is a shared-resource/interconnect problem outside the
scope of the per-block optimization taxonomy used here.

GMU comparison, for anyone reproducing the 116 MHz comparison point: the -1 vs
-3 speed grade accounts for most of the gap (68.5 to 94.1 MHz); constraint
targeting at 8.62 ns on -3 grade reaches 96.2 MHz optimized. The remaining ~17%
gap to GMU's reported 116 MHz is attributed to the directive/frequency-search
class (GMU's Minerva tool iterates multiple targets automatically; this project
ran a single fixed target per corner). Before citing GMU's numbers directly,
verify their exact device grade, Vivado version, and flow stage against the
source paper. These are noted as unconfirmed pending citation-check in the
project's own findings.
