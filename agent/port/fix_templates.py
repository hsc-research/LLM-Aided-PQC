"""Cross-toolchain port defect taxonomy and fix templates.

Derived from findings F1, F4, F5, F8, F9, F10 in docs/findings/asic/.

AUTONOMY is the key field. A fix is autonomous only if it is *supposed* to be
a pure reordering, so that the sorted-diff check is meaningful. Fixes that
change semantics by design cannot be gated that way and require a human.
"""

TEMPLATES = {
    "VLOGPT-20": {
        "name": "use_before_declaration",
        "fix": "hoist declaration above first use, at module scope",
        "pure_reorder": True,
        "autonomous": True,
        "constraint": (
            "Destination MUST be module scope, adjacent to the existing "
            "declaration block. Inserting immediately above first use can land "
            "inside a procedural block, where reg declarations are illegal. "
            "The sorted-diff check will NOT catch this (F8 sub-finding); only "
            "the tool will."
        ),
        "seen_in": ["poly_mult.v", "v_minus_uy.v", "combined_top.v"],
    },
    "VLOGPT-22": {
        "name": "duplicate_declaration",
        "fix": "remove the redundant declaration",
        "pure_reorder": False,          # deletion, not reorder
        "autonomous": True,
        "constraint": (
            "Only autonomous when the two declarations are byte-identical "
            "modulo whitespace. A differing width or type is intentional "
            "shadowing or a real bug: refuse and escalate."
        ),
        "seen_in": ["v_minus_uy.v"],
    },
    "CDFG-238": {
        "name": "mixed_blocking_nonblocking",
        "fix": "convert blocking assignments to non-blocking",
        "pure_reorder": False,
        "autonomous": False,            # F9: changes semantics by design
        "constraint": (
            "NOT autonomous. Equivalence depends on assignment ordering within "
            "the block and cannot be established mechanically. Requires human "
            "reasoning plus full KAT. Escalate."
        ),
        "seen_in": ["ntt_fifo_piso.v"],
    },
    "VLOGPT-1": {
        "name": "parse_error",
        "fix": None,
        "autonomous": False,
        "constraint": (
            "Usually a cascade artifact or the result of a bad prior edit. "
            "Revert to .bak and escalate; do not attempt a fix."
        ),
        "seen_in": [],
    },
}

# Not defects. Build configuration errors that produce defect-shaped symptoms.
BUILD_ERRORS = {
    "CDFG-428": (
        "Blackbox created. Either a deliberate memory blackbox or a MISSING "
        "SOURCE FILE. Check the blackbox count against the expected memory "
        "count before trusting any number (F10). ML-DSA's Keccak is VHDL and "
        "was silently blackboxed by a Verilog-only glob."
    ),
    "VHDLPT-703": (
        "No such primary unit. VHDL package read order, not a defect. "
        "Packages must be read before their users; alphabetical glob fails."
    ),
}


def classify(error_code):
    if error_code in TEMPLATES:
        return "defect", TEMPLATES[error_code]
    if error_code in BUILD_ERRORS:
        return "build_config", {"note": BUILD_ERRORS[error_code]}
    return "unknown", {}
