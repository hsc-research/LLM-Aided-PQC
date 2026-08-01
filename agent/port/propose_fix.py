"""Propose a port fix for a classified defect.

The model returns a STRUCTURED EDIT (anchor plus replacement), never free-form
RTL. Deterministic code applies it and the three-stage gate accepts or rejects.
The model cannot influence any check.
"""
import os, sys, json, re
import anthropic

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_templates import TEMPLATES

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM = """You fix Verilog cross-toolchain portability defects.

Rules, without exception:
1. Output ONLY a JSON object. No prose, no markdown fences.
2. Never change logic. These fixes are declaration movements or deletions.
3. For a hoist, the destination MUST be module scope, adjacent to existing
   module-scope declarations. Never inside an always block, initial block,
   generate block, or task. A reg declaration inside a procedural block is
   illegal Verilog even though moving it there is a pure reordering.
4. Anchors must be byte-exact including leading whitespace, and must appear
   exactly once in the file.
5. If you cannot construct a byte-exact unique anchor, or the fix is not
   clearly semantics-preserving, return {"verdict":"refuse","reason":"..."}.

Schema for a proposed fix:
{"verdict":"edit",
 "remove":"<exact text to delete, or empty string>",
 "anchor":"<exact unique line the insertion goes AFTER>",
 "insert":"<exact text to insert>",
 "rationale":"<one sentence>"}"""


def propose(code, filename, source, error_text):
    tpl = TEMPLATES.get(code, {})
    if not tpl.get("autonomous"):
        return {"verdict": "refuse",
                "reason": f"{code} is not autonomous: {tpl.get('constraint','')}"}
    prompt = f"""Defect: {code} ({tpl.get('name')})
Prescribed fix: {tpl.get('fix')}
Constraint: {tpl.get('constraint')}

Tool error:
{error_text}

File: {filename}
--- SOURCE ---
{source}
--- END SOURCE ---

Return the JSON object."""
    r = client.messages.create(model=MODEL, max_tokens=2000,
                               system=SYSTEM,
                               messages=[{"role": "user", "content": prompt}])
    txt = "".join(b.text for b in r.content if b.type == "text").strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
    try:
        out = json.loads(txt)
    except json.JSONDecodeError:
        return {"verdict": "refuse", "reason": "unparsable model output"}
    out["_usage"] = {"in": r.usage.input_tokens, "out": r.usage.output_tokens}
    return out


def _nl(t):
    """Normalize to exactly one trailing newline. The model formats
    inconsistently; deterministic code owns line structure."""
    return t.rstrip("\n") + "\n" if t else t


def apply_edit(path, edit):
    """Deterministic application with uniqueness asserts. Returns (ok, msg).

    Newlines are normalized here rather than trusted from the model. Without
    this, an anchor lacking a trailing newline concatenates two declarations
    onto one line, which is legal Verilog but breaks the line-based
    sorted-diff check in port_gate.stage1.
    """
    s = open(path).read()

    if edit.get("remove"):
        rem = _nl(edit["remove"])
        n = s.count(rem)
        if n != 1:
            return False, f"remove text appears {n} times, need exactly 1"
        s = s.replace(rem, "", 1)

    anchor = edit.get("anchor", "")
    if anchor:
        anc = _nl(anchor)
        n = s.count(anc)
        if n != 1:
            return False, f"anchor appears {n} times, need exactly 1"
        ins = _nl(edit.get("insert", ""))
        s = s.replace(anc, anc + ins, 1)

    open(path, "w").write(s)
    return True, "applied"
