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
0. Fix EVERY use-before-declaration in the file, not only the symbols the
   tool happened to report. The tool stops at its first error cluster, but you
   can see the whole file. If several separate declaration blocks are each
   used before they are declared, return a list of moves.
4. You identify WHICH lines move by number. You never reproduce their text.
   The source is given with 1-indexed line numbers. Deterministic code moves
   the original bytes verbatim, so whitespace is preserved automatically.
5. first_line..last_line must cover the whole contiguous declaration block,
   including any blank or whitespace-only lines inside it.
6. after_line is a line number in the ORIGINAL numbering. The block is placed
   immediately after it, and it must be at module scope.
7. If the fix is not clearly semantics-preserving, or the declarations are not
   contiguous, return {"verdict":"refuse","reason":"..."}.

Schema for a proposed fix (all line numbers refer to the ORIGINAL file):
{"verdict":"move",
 "moves":[{"first_line":<int>,"last_line":<int>,"after_line":<int>}, ...],
 "rationale":"<one sentence>"}"""


def propose(code, filename, source, error_text):
    tpl = TEMPLATES.get(code, {})
    if not tpl.get("autonomous"):
        return {"verdict": "refuse",
                "reason": f"{code} is not autonomous: {tpl.get('constraint','')}"}
    numbered = "\n".join(f"{i}: {l}" for i, l in enumerate(source.split("\n"), 1))
    prompt = f"""Defect: {code} ({tpl.get('name')})
Prescribed fix: {tpl.get('fix')}
Constraint: {tpl.get('constraint')}

Tool error:
{error_text}

File: {filename}
--- SOURCE (1-indexed) ---
{numbered}
--- END SOURCE ---

Return the JSON object."""
    r = client.messages.create(model=MODEL, max_tokens=4000,
                               system=SYSTEM,
                               messages=[{"role": "user", "content": prompt}])
    txt = "".join(b.text for b in r.content if b.type == "text").strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
    # The model sometimes prefixes prose despite rule 1. Extract the outermost
    # JSON object rather than assuming the whole response is JSON.
    if not txt.startswith("{"):
        i = txt.find("{")
        if i >= 0:
            depth, j = 0, i
            for j in range(i, len(txt)):
                if txt[j] == "{": depth += 1
                elif txt[j] == "}":
                    depth -= 1
                    if depth == 0: break
            txt = txt[i:j+1]
    try:
        out = json.loads(txt)
    except json.JSONDecodeError:
        return {"verdict": "refuse", "reason": "unparsable model output",
                "raw": txt[:600]}
    out["_usage"] = {"in": r.usage.input_tokens, "out": r.usage.output_tokens}
    return out


def apply_move(path, first_line, last_line, after_line):
    """Move lines [first_line, last_line] to just after after_line, 1-indexed.

    The model identifies WHICH lines move; this code moves the original bytes
    verbatim. Asking the model to reproduce whitespace it cannot see reliably
    caused spurious stage-1 failures on lines with trailing spaces.
    """
    lines = open(path).readlines()
    n = len(lines)
    if not (1 <= first_line <= last_line <= n and 1 <= after_line <= n):
        return False, f"line range out of bounds (file has {n} lines)"
    if first_line <= after_line <= last_line:
        return False, "destination is inside the moved block"
    block = lines[first_line-1:last_line]
    rest  = lines[:first_line-1] + lines[last_line:]
    # after_line refers to the ORIGINAL numbering; adjust if it sat below block
    dest = after_line if after_line < first_line else after_line - len(block)
    out = rest[:dest] + block + rest[dest:]
    open(path, "w").writelines(out)
    return True, f"moved {len(block)} lines from {first_line}-{last_line} to after {after_line}"


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
