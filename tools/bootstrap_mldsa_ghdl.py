#!/usr/bin/env python3
"""Download/extract the pinned official Debian GHDL toolchain locally.

This explicitly invoked setup helper does not use root, apt, or system paths.
Requires network access, dpkg-deb, and a compatible Linux x86-64 runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import urllib.request

PACKAGES = (
    ("ghdl-mcode", "6.0.0+dfsg3-1", "f78203381ee4ca00210f245bbb7dfb0c7dea44ec2cbdd7bfbfae669fa1c4f921", "root"),
    ("ghdl-common", "6.0.0+dfsg3-1", "399a4bec476e3edb2b51c76c460bc5bb835fe69257b67f34097815c46c8b8c15", "root"),
    ("ghdl-common", "5.0.1+dfsg-1+b1", "f205ba98df92d34ee8ee05fc5f071d51c9503626879f0d5dc225510f5c2810e9", "compat"),
)


def install(prefix):
    prefix = Path(prefix).resolve()
    prefix.mkdir(parents=True, exist_ok=True)
    packages = prefix / "packages"; packages.mkdir(exist_ok=True)
    manifest = {"packages": [], "commands": []}
    for name, version, digest, destination in PACKAGES:
        filename = f"{name}_{version}_amd64.deb"
        url = "https://deb.debian.org/debian/pool/main/g/ghdl/" + filename
        path = packages / filename
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"official-package SHA-256 mismatch: {filename}")
        command = ["dpkg-deb", "-x", str(path), str(prefix/destination)]
        subprocess.run(command, check=True)
        manifest["commands"].append(command)
        manifest["packages"].append({"name": name, "version": version, "url": url,
                                      "sha256": digest, "bytes": path.stat().st_size})
    binary = prefix / "root/usr/bin/ghdl-mcode"
    library = prefix / "root/usr/lib/ghdl/mcode/vhdl"
    bindir = prefix / "bin"; bindir.mkdir(exist_ok=True)
    wrapper = bindir / "ghdl"
    wrapper.write_text("#!/bin/sh\nexport GHDL_PREFIX=" + shlex.quote(str(library)) +
                       "\nexec " + shlex.quote(str(binary)) + ' "$@"\n')
    wrapper.chmod(0o755)
    compatibility = prefix / "compat/usr/lib/ghdl/src/synopsys"
    sources = [compatibility/(name+".vhdl") for name in ("std_logic_arith", "std_logic_unsigned")]
    command = [str(wrapper), "-a", "--std=08", "-fsynopsys", "--work=ieee",
               "--workdir="+str(library/"ieee/v08"), *map(str, sources)]
    subprocess.run(command, check=True)
    manifest["commands"].append(command)
    manifest["source_and_executable_hashes"] = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [binary, wrapper, *sources]}
    manifest["version"] = subprocess.check_output([str(wrapper), "--version"], text=True)
    (prefix / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    return {"bin": str(bindir), "manifest": str(prefix/"manifest.json"), "version": manifest["version"].splitlines()[0]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, help="local extraction directory, e.g. /tmp/pqc-ghdl")
    print(json.dumps(install(parser.parse_args().prefix), indent=2))
