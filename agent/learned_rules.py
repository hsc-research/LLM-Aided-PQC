"""Append-only machine-derived optimization rules with provenance.
Injected into orchestrator prompts AFTER the hand-written POLICY with an
explicit precedence note (hand-written POLICY wins on conflict).
Each rule carries a pointer to the log line (evidence) that produced it."""
import os, json, time
from pathlib import Path
try:
    from .experiment_history import is_final_acceptance, latest_records
except ImportError:
    from experiment_history import is_final_acceptance, latest_records
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "learned_rules.jsonl")

def append_rule(rule_text, evidence, design, source_model):
    if not is_final_acceptance(evidence):
        raise ValueError('Learned rules require a final whole-design acceptance record')
    rec = {"ts": time.strftime("%F %T"), "design": design,
           "rule": rule_text.strip(), "evidence": evidence['candidate_id'],
           "evidence_stage": "full_design", "history_schema": 1,
           "history_state": "finally_accepted", "source_model": source_model}
    with open(RULES, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def rules_prompt_block(design=None, max_rules=40):
    """Render learned rules for prompt injection. Newest last (recency visible)."""
    if not os.path.exists(RULES):
        return ""
    final_ids = {r['candidate_id'] for r in latest_records() if is_final_acceptance(r)}
    recs = []
    for line in Path(RULES).read_text().splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (isinstance(record, dict) and record.get('history_schema') == 1
                and record.get('history_state') == 'finally_accepted'
                and record.get('evidence_stage') == 'full_design'
                and isinstance(record.get('evidence'), str)
                and record.get('evidence') in final_ids
                and isinstance(record.get('rule'), str)):
            recs.append(record)
    if design:
        recs = [r for r in recs if r.get("design") in (design, "all")]
    recs = recs[-max_rules:]
    if not recs:
        return ""
    lines = [f"- [{r['design']}] {r['rule']}" for r in recs]
    return ("\n\nMACHINE-LEARNED RULES (append-only, evidence-backed; the "
            "hand-written strategy menu above WINS on any conflict):\n"
            + "\n".join(lines))

def distill_rule(client, model, verdict_rec, design):
    """Ask the model to distill one transferable rule from a verdict record."""
    if not is_final_acceptance(verdict_rec):
        raise ValueError('Rule distillation requires final whole-design acceptance')
    prompt = (
        "You are maintaining an optimization rulebook for FPGA PPA agents. "
        "From this single experiment record, write EXACTLY ONE transferable "
        "rule (<=40 words) that would help a future agent pick or avoid a "
        "strategy. State conditions, not just outcomes. Reply with only the "
        "rule text.\n\nRECORD:\n" + json.dumps(verdict_rec, indent=1))
    r = client.messages.create(model=model, max_tokens=120,
                               messages=[{"role": "user", "content": prompt}])
    txt = r.content[0].text.strip()
    return append_rule(txt, verdict_rec, design, model)
