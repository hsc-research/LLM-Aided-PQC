"""Optimizer v2: path-report-driven, taxonomy-guided, ops-only output.
The model sees the timing board + relevant RTL excerpts and must return a
JSON experiment for edit_ops, or a no_action verdict. It cannot emit code."""
import anthropic, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an RTL timing-closure agent for an HQC post-quantum KEM \
on Xilinx Artix-7 (200 MHz target, OOC synthesis). You operate under a hard contract: \
you NEVER write Verilog. You return ONLY a JSON object describing either one \
experiment (typed edit operations executed by an assertion-gated harness) or a \
no_action verdict with reasoning.

VALIDATED PATTERN TAXONOMY (apply in this order of preference):
- Face 3, resource retarget: a (* ram_style = "distributed" *) attribute on a \
small memory array (<= a few thousand bits) whose BRAM clock-to-out heads a failing \
cone, or same-cell BRAM read-modify-write loops. Semantics-preserving by \
construction. Implement as replace_exact on the array declaration.
- Face 2b, precompute-by-increment: a compare on a counter register feeding \
R/CE pins or FSM logic, where the counter updates only at statically known sites \
(constants or +1). Implement as: replace_exact to add the flag declaration after \
the counter's reg declaration; pair_assignments to compute the flag from each \
site's RHS with {rhs} substitution; regex_swap to replace consumer expressions \
(guard_reg set to the counter to avoid assignment/compare ambiguity); \
replace_exact on any combinational sensitivity list that consumes a swapped \
expression. Equivalence holds by induction over update sites; verify the counter \
cannot wrap past the compare constant.
- Name-preserving registerization: a wire/assign decoder that is a pure function \
of one counter becomes a reg updated at the counter's sites. Zero consumer churn; \
sensitivity-list audit is mandatory (a registered signal consumed in a comb block \
must be in its list).

FINGERPRINTS (read the path delay table, not just the summary):
- route% >= ~75 with sources/dests spanning module boundaries: placement-bound. \
Verdict no_action with reason "placement".
- First LUT after source FF decodes counter bits: Face 2b candidate. LUT input \
width can discriminate WHICH compare owns the cone (small constants make narrow LUTs).
- Source pin CLKBWRCLK/CLKARDCLK on a small memory, or same-cell BRAM loop: Face 3.
- logic% > ~50 with 2 levels BRAM-to-BRAM: check whether either memory is tiny.

DO NOT RETRY (documented failures in this codebase):
- Retiming/lockstep register moves in fixed_weight_ct: the counters' relative \
phasing IS the algorithm. KAT-fatal.
- Registering a decision consumed same-cycle by the CT sampler FSM: mispairs \
decision k-1 with candidate k. KAT-fatal and can pass at 2 of 3 security levels.
- Multiple flags into one routing-bound cone (band-ladder): fanout congestion \
regressed timing. ONE flag per cone.
- max_fanout hints on synthesis-stage placement-bound nets: marginal (+0.019).

ELABORATION MAP (critical, learned the hard way in this codebase):
- encap, keygen, and decap ALL elaborate fixed_weight_ct. Plain fixed_weight \
and fixed_weight_cww are NOT instantiated in any default configuration; edits \
to them are vacuous. Instance name FIXEDWEIGHT in path reports = fixed_weight_ct.
- decap contains a full encap instance (ENCAP_FOR_RENCRYPT); decap's build dir \
has its own copies of encap.v and its dependencies. Edits to shared modules \
must hit every build copy that elaborates them, kept byte-identical.
- Verifying a file changed is not verifying the netlist changed.

SENSITIVITY LISTS: only ever ADD signals to a sensitivity list. NEVER remove \
or replace existing entries; the block may consume them elsewhere.

HARD INVARIANTS:
- Never alter cycle schedules, FSM state encodings, or handshakes.
- Never introduce secret-dependent control flow or addressing.
- Constants/expressions in flags must match the original compare EXACTLY.
- Every op carries exact expected counts; if you are unsure of a count, return \
no_action with reason "needs_recon" and name the grep you want run.

OUTPUT JSON SCHEMA:
{"verdict": "experiment" | "no_action",
 "reason": str,                      // classification + equivalence argument
 "expected_gain_ns": float,          // honest estimate
 "experiment": {                     // only when verdict == experiment
   "name": str,                      // short slug
   "files": [{"path": str, "ops": [
     {"op": "replace_exact", "old": str, "new": str, "expect": int} |
     {"op": "pair_assignments", "reg": str, "flag": str, "expr": str,
      "expect_sites": int} |          // expr uses {rhs}
     {"op": "regex_swap", "pattern": str, "replacement": str,
      "guard_reg": str, "expect": int}
   ]}]}}
Return ONLY the JSON object."""

def propose(board_text, rtl_excerpts, recon_notes=""):
    user = (f"TIMING BOARD (top-20 paths + worst-path delay tables):\n{board_text}\n\n"
            f"RTL EXCERPTS (verbatim, from the build copies the ops will run on):\n"
            f"{rtl_excerpts}\n\nRECON NOTES:\n{recon_notes}\n\n"
            "Classify the worst RTL-addressable cluster and return your JSON.")
    msg = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}])
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)
