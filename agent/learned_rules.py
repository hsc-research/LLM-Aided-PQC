"""Append-only machine-derived optimization rules with provenance.
Injected into orchestrator prompts AFTER the hand-written POLICY with an
explicit precedence note (hand-written POLICY wins on conflict).
Each rule carries a pointer to the log line (evidence) that produced it."""
import os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "learned_rules.jsonl")

def append_rule(rule_text, evidence, design, source_model):
    rec = {"ts": time.strftime("%F %T"), "design": design,
           "rule": rule_text.strip(), "evidence": evidence,
           "source_model": source_model}
    with open(RULES, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def rules_prompt_block(design=None, max_rules=40):
    """Render learned rules for prompt injection. Newest last (recency visible)."""
    if not os.path.exists(RULES):
        return ""
    recs = [json.loads(l) for l in open(RULES) if l.strip()]
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
    prompt = (
        "You are maintaining an optimization rulebook for FPGA PPA agents. "
        "From this single experiment record, write EXACTLY ONE transferable "
        "rule (<=40 words) that would help a future agent pick or avoid a "
        "strategy. State conditions, not just outcomes. Reply with only the "
        "rule text.\n\nRECORD:\n" + json.dumps(verdict_rec, indent=1))
    r = client.messages.create(model=model, max_tokens=120,
                               messages=[{"role": "user", "content": prompt}])
    txt = r.content[0].text.strip()
    return append_rule(txt, verdict_rec.get("ts") or time.strftime("%F %T"),
                       design, model)
