#!/usr/bin/env python3
"""Run the already-installed YoWASP Yosys with bounded, per-process larger stack.

The tool package and Wasm module are unchanged. No software is downloaded and no
system setting is changed. The 16 MiB Wasm limit stays below its 32 MiB OS thread
stack. This addresses the default 2 MiB TopoSort stack exhaustion on ML-DSA.
Set PYTHONPATH to the installed YoWASP package directory before invoking.
"""
import sys, threading
import wasmtime
from wasmtime import _bindings
import yowasp_yosys
_original_config = wasmtime.Config

def _config():
    config = _original_config()
    _bindings.wasmtime_config_async_stack_size_set(config.ptr(), 32 * 1024 * 1024)
    config.max_wasm_stack = 16 * 1024 * 1024
    return config

wasmtime.Config = _config
threading.stack_size(32 * 1024 * 1024)
sys.exit(yowasp_yosys._run_yosys_argv())
