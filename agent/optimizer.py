# HQC Agent - Optimizer
# Sends a Verilog module to Claude and asks for a PPA-improved version.

import anthropic
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from synthesizer import run_synthesis
from baseline import compare

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an expert RTL hardware designer optimizing Verilog code for FPGA implementation on a Xilinx Artix-7.
Your goal is to reduce LUT count, flip-flop count, and improve timing (Fmax) without changing functional behavior.

Rules you must never violate:
- The module interface (ports and names) must stay exactly the same
- Functional output must be identical to the original
- No secret-dependent control flow or memory access patterns
- Fixed cycle count per operation must be preserved
- No new latches or uninitialized state

When given a Verilog module, return ONLY the improved Verilog code with no explanation, no markdown, no code fences.
Just the raw Verilog starting with the module declaration."""

def load_verilog(filepath):
    with open(filepath, "r") as f:
        return f.read()

def save_verilog(filepath, code):
    with open(filepath, "w") as f:
        f.write(code)

def strip_fences(code):
    lines = code.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)

def ask_claude(verilog_code, previous_error=None):
    if previous_error:
        user_msg = (
            f"Your previous optimization attempt failed with this Vivado error:\n"
            f"{previous_error}\n\n"
            f"Please try a different optimization strategy that avoids this error.\n"
            f"Do not modify bit-selects or signal widths.\n\n"
            f"Here is the original Verilog to optimize:\n\n{verilog_code}"
        )
    else:
        user_msg = f"Optimize this Verilog module for FPGA PPA:\n\n{verilog_code}"

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_msg}
        ]
    )
    return strip_fences(message.content[0].text)

def optimize_once(module, param_set, verilog_path, backup=True, previous_error=None):
    original = load_verilog(verilog_path)
    backup_path = verilog_path + ".backup"

    if backup:
        save_verilog(backup_path, original)
        print(f"Backup saved to {backup_path}")

    print("Sending to Claude for optimization...")
    optimized = ask_claude(original, previous_error=previous_error)
    save_verilog(verilog_path, optimized)

    print("Running synthesis on optimized version...")
    result = run_synthesis(module, param_set)

    if "error" in result:
        print(f"Synthesis failed: {result['error']}")
        print("Restoring original file from backup...")
        save_verilog(verilog_path, original)
        return {"status": "failed", "reason": result["error"]}

    delta = compare(result)
    return {"status": "ok", "result": result, "delta": delta}

if __name__ == "__main__":
    output = optimize_once(
        module       = "poly_mult",
        param_set    = "hqc128",
        verilog_path = "./build/keygen/poly_mult.v"
    )
    print("\n--- Status:", output["status"])
    if output["status"] == "ok":
        print("\n--- PPA Result ---")
        print(output["result"])
        print("\n--- Delta vs Baseline ---")
        for metric, info in output["delta"].items():
            print(metric, info)
    else:
        print("Reason:", output["reason"])
