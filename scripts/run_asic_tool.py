#!/usr/bin/env python3
"""Convenience entry point for the Genus/DC fixed-period synthesis runner."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.asic_synthesis import main

if __name__ == '__main__':
    sys.exit(main())
