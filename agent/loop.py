# HQC Agent - Optimization Loop
# Iterates optimize -> synthesize -> compare, keeping the best result.

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from optimizer import optimize_once, load_verilog, save_verilog

def run_loop(module, param_set, verilog_path, max_iterations=10):
    print(f"Starting optimization loop: {module} / {param_set}")
    print(f"Max iterations: {max_iterations}")
    print("="*50)

    best_result  = None
    best_code    = load_verilog(verilog_path)
    history      = []
    last_error   = None

    for i in range(max_iterations):
        print(f"\nIteration {i+1} of {max_iterations}")

        save_verilog(verilog_path, best_code)

        output = optimize_once(
            module         = module,
            param_set      = param_set,
            verilog_path   = verilog_path,
            backup         = False,
            previous_error = last_error
        )

        if output["status"] == "failed":
            print(f"  Synthesis failed, feeding error back to Claude")
            last_error = output["reason"]
            history.append({"iteration": i+1, "status": "failed"})
            save_verilog(verilog_path, best_code)
            continue

        last_error = None
        result = output["result"]
        delta  = output["delta"]

        improvements = [m for m, d in delta.items() if d["better"]]
        regressions  = [m for m, d in delta.items() if not d["better"] and d["change"] != 0]

        print(f"  LUTs: {result['luts']}  FFs: {result['ffs']}  Fmax: {result['fmax_mhz']} MHz  WNS: {result['wns_ns']} ns")
        print(f"  Improved: {improvements}")
        print(f"  Worse:    {regressions}")

        history.append({
            "iteration":    i+1,
            "status":       "ok",
            "luts":         result["luts"],
            "ffs":          result["ffs"],
            "fmax_mhz":     result["fmax_mhz"],
            "wns_ns":       result["wns_ns"],
            "improvements": improvements,
            "regressions":  regressions
        })

        lut_delta = delta["luts"]["change"]
        wns_delta = delta["wns_ns"]["change"]

        if lut_delta < 0 or wns_delta > 0:
            if best_result is None or result["luts"] <= best_result["luts"]:
                print(f"  New best result, keeping this version")
                best_result = result
                best_code   = load_verilog(verilog_path)
            else:
                print(f"  Some improvement but not better overall, keeping previous best")
                save_verilog(verilog_path, best_code)
        else:
            print(f"  No improvement, reverting to best known")
            save_verilog(verilog_path, best_code)

    print("\n" + "="*50)
    print("Loop complete")
    if best_result:
        print(f"Best result found:")
        print(f"  LUTs: {best_result['luts']}  FFs: {best_result['ffs']}  Fmax: {best_result['fmax_mhz']} MHz")
    else:
        print("No improvement found over baseline")

    save_verilog(verilog_path, best_code)
    return {"best": best_result, "history": history}

if __name__ == "__main__":
    run_loop(
        module         = "poly_mult",
        param_set      = "hqc128",
        verilog_path   = "./build/keygen/poly_mult.v",
        max_iterations = 5
    )
