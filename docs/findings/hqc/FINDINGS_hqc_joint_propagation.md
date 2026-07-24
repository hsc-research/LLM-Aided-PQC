# FINDINGS: HQC joint composition silently reverted by a1a7ad2, restored

**Verdict: for three days `hqc_joint_opt` synthesized effectively-pristine RTL.
Restoring the composition moved true closure 114.8 to 116.0 MHz (+1.0%), after
which the design binds on the shared Keccak state RAM.**

## The defect

`a1a7ad2` added a glob to `_hqc_joint_opt()` in `agent/synthesizer.py`:

```python
for p in _g.glob("./build/joint_design/*.v"):
    pris[_o.path.basename(p)] = p
```

It runs **after** the `SWAP` block that pulls win-carrying files from
`build/{keygen,encap,decap}`, so it overwrites them. Verified against history:

```bash
git show a1a7ad2^:agent/synthesizer.py | grep -n "joint_design"   # no glob
git show a1a7ad2:agent/synthesizer.py  | grep -n "joint_design"   # glob at line 143
```

The overwrite was silent because `build/joint_design/*.v` were **untracked**,
and `joint_kat_gate.stage()` regenerates them from pristine on every run:

```python
for pat in srcs:                       # hardware/**/*.v
    shutil.copy(p, "build/joint_design/")
subprocess.run(["git","checkout","--","build/joint_design/"])   # tracked only
```

`git checkout --` restores from the index, so it only protects **tracked**
files. Untracked ones keep the pristine copy that `stage()` just wrote.

## Why it was invisible

Both the gate and the synthesizer read the same overwritten tree, so the KAT
passed and the flow reported a valid-looking number. The result was a
composition that was pristine in everything but name.

Note this makes the failure mode worse than a vacuous gate: the gate was
correct, the synthesis was correct, and both were operating on RTL that had
silently lost its edits.

## Vacuity probe (reusable)

Two commands establish whether an edit survives the gate's staging step:

```bash
echo "// PROBE" >> build/joint_design/decap.v
git checkout -- build/joint_design/
grep -c "PROBE" build/joint_design/decap.v     # 0 = wiped, edit cannot be gated

echo "// PROBE2" >> build/joint_design/decap.v
git add build/joint_design/decap.v
git checkout -- build/joint_design/
grep -c "PROBE2" build/joint_design/decap.v    # 1 = staged edits survive
```

Measured: **0 then 1.** Any orchestrator writing to this tree must `git add`
after applying or its gate result is meaningless.

## The fix

Copy the win-carrying files into `build/joint_design/` and **track** them, so
`stage()`'s checkout restores the wins instead of the pristine copies. Ten
files: `encap.v`, `encrypt_parallel.v`, `encrypt.v`, `fixed_weight_ct.v`,
`fixed_weight.v`, `hqc_rsdecod_err_val.v`, `syncfifo.v`, `xor_based_adder.v`,
`v_minus_uy.v`, and `mem_single_dist.v`.

`mem_single_dist.v` was found only by an elaboration failure:

```
ERROR: [VRFC 10-2063] Module <mem_single_dist> not found while processing
module instance <MSG_MEM> [build/joint_design/encap.v:272]
```

It is a **new** module introduced by VERIFIED WIN #6 (MSG_MEM retargeted to
distributed RAM). It never existed in `hardware/`, so `stage()` had no source
to copy and no mechanism would ever have supplied it. Any win that adds a
module, rather than editing one, has this exposure.

## Measurements

Same flow throughout: `regen_ckpt` at 8.600 ns, OOC, then `fmax_search`
binary search to true closure (`ExtraTimingOpt` / `Explore` / `Explore`,
accept only `Slack (MET)`).

| Build | Closing period | Closing fmax | WNS at close |
|---|---|---|---|
| `hqc_joint_pristine` | 8.71 ns | 114.8 MHz | +0.057 |
| `hqc_joint_opt`, pre-propagation | 8.68 ns | 115.2 MHz | +0.061 |
| `hqc_joint_opt`, propagated | 8.62 ns | **116.0 MHz** | +0.006 |

The middle row is the evidence: **pre-propagation `opt` measured within 0.35%
of pristine**, which is noise. The composition was inert, exactly as the code
path predicts.

Joint KAT PASS on HQC-128/192/256 after propagation, and the override survived
a full `stage()` cycle (re-checked post-gate, all ten files still non-pristine).

Prior numbers `117.1` and `119.3` were measured **before** `a1a7ad2` from
`synth_out/sweep_hqc_joint_*` checkpoints and remain valid; they used a
different regen period and are not directly comparable to the triple above.
The `114.3` figure logged in `chip_orchestrator_log.jsonl` is post-`a1a7ad2`
and therefore measured pristine plus the mux edit only.

## Related: mux retiming reverted

The registered one-hot client-select mux (`a1a7ad2`, restored by `d105e35`)
was KAT-clean at all three security levels but did not survive post-route
judgment. Reverted by `git apply -R` of the isolated hunk; joint KAT re-run
PASS. Documented as a negative: latency-neutral and correctness-clean is not
sufficient, post-route closure is the judge.

## Where HQC now binds

Top 5 paths at the 8.62 ns closure point:

| Slack | Source | Destination |
|---|---|---|
| 0.006 | `SHAKE256/control_path_instance/counter_reg[5]` | `SHAKE256/.../state_ram/ram_generator[0]` |
| 0.080 | `DECAP_MODULE/FSM_sequential_state_reg[3]` | `ENCAP_MODULE/HASH_MEM/mem_reg_0/DIADI[7]` |
| 0.090 | `DECAP_MODULE/FSM_sequential_state_reg[3]` | `SHAKE256/.../ram_generator[23]` |
| 0.093 | `DECAP_MODULE/FSM_sequential_state_reg[3]` | `SHAKE256/.../ram_generator[17]` |
| 0.103 | `DECAP_MODULE/FSM_sequential_state_reg[3]` | `SHAKE256/.../ram_generator[11]` |

Four of five terminate in the shared Keccak state RAM. The cluster spans
0.006 to 0.103 ns, so eliminating the worst path entirely buys 0.074 ns before
the next binds: 8.62 to 8.546 ns, about +0.9%. This is a converged design, not
one with a single removable spike.

Deshpande et al. (PQC 2022) report the same wall on this architecture: they
explored pipelining the critical path, found several such paths, and concluded
the cycle-count overhead outweighed the frequency gain. Speed grade differs
(their tables are `-3`, ours is `-1`), so their absolute numbers are not
directly comparable, but the terminus is.

ML-DSA reached the same place: its chip loop also ended on shared-Keccak
interconnect. Two PQC families, two independent campaigns, one shared
primitive as the floor.

## What this changes

1. Per-block wins **do** compose at the chip level once actually delivered:
   +1.0% over pristine. The earlier apparent null was infrastructure, not
   architecture.
2. Untracked build trees are an active hazard wherever a gate regenerates
   sources. Track them, or the gate validates something other than what
   synthesis sees.
3. Wins that introduce new modules need explicit propagation; file-for-file
   copying will not find them.

## Reproduction

```bash
python3 -c "
import sys; sys.path.insert(0,'agent')
from chip_orchestrator import regen_ckpt
regen_ckpt({'key':'hqc_joint_opt','ckpt':'build/joint_design/x.dcp','regen_period_ns':8.600})"
python3 agent/fmax_search.py build/joint_design/x.dcp hqc_prop 8.0 9.5
```

Expect `closing_period_ns 8.62`, `closing_fmax_mhz 116.0`.
