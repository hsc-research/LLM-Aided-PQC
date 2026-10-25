#!/usr/bin/env python3
"""Check the vendored snapshot, manifests, wrapper presence, and vector coverage.

This is an integrity check, not functional verification or an EDA compile.
Only Python's standard library is used; no upstream code is imported/executed.
"""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    upstream = root / "upstream"
    manifest = json.loads((upstream / "SOURCE_MANIFEST.json").read_text())
    if manifest["commit"] != "b77e3d899e828d626cfc2a0d26a6b5704cc121e0":
        raise SystemExit("FAIL: unexpected upstream commit")
    for item in manifest["files"]:
        data = (upstream / item["path"]).read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        if len(data) != item["size"] or hashlib.sha1(blob).hexdigest() != item["sha"]:
            raise SystemExit("FAIL: upstream blob mismatch: " + item["path"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit("FAIL: SHA256 mismatch: " + item["path"])
    config = json.loads((root / "integration/manifest.json").read_text())
    if config["top"] != "abr_unified_top":
        raise SystemExit("FAIL: unexpected integration top")
    for item in config["files"]:
        if not (root / item["path"]).is_file():
            raise SystemExit("FAIL: missing source: " + item["path"])
    for directory in config["include_dirs"]:
        if not (root / directory).is_dir():
            raise SystemExit("FAIL: missing include directory: " + directory)
    lines = (root / "integration/sources.f").read_text().splitlines()
    listed_files = [line for line in lines if line and not line.startswith("+")]
    if listed_files != [item["path"] for item in config["files"]]:
        raise SystemExit("FAIL: file lists disagree")
    vector_manifest = json.loads((root / "test_vectors/DERIVED_MANIFEST.json").read_text())
    for item in vector_manifest["files"]:
        data = (root / "test_vectors" / item["path"]).read_bytes()
        if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit("FAIL: test-vector provenance file mismatch: " + item["path"])
    vectors = json.loads((root / "test_vectors/nist_acvp_mlkem1024.json").read_text())
    counts = {}
    identities = set()
    for case in vectors["cases"]:
        key = (case["operation"], case["tgId"], case["tcId"])
        if key in identities:
            raise SystemExit("FAIL: duplicate ACVP vector")
        identities.add(key)
        counts[case["operation"]] = counts.get(case["operation"], 0) + 1
        if not case["expected"]:
            raise SystemExit("FAIL: missing expected output")
    expected_counts = {"keyGen": 25, "encapsulation": 25, "decapsulation": 10,
                       "encapsulationKeyCheck": 10, "decapsulationKeyCheck": 10}
    if counts != expected_counts:
        raise SystemExit("FAIL: unexpected ACVP vector coverage")
    print(f"PASS: {len(manifest['files'])} upstream files are byte-identical; "
          f"{len(config['files'])} compile entries exist; 80 ACVP cases present.")
    print("NOT RUN: RTL compile, RTL simulation, equivalence, synthesis, PPA, side-channel tests.")


if __name__ == "__main__":
    main()
