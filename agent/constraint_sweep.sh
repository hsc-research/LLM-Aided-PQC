#!/bin/bash
cd /mnt/c/PQC/hqc
for p in 8.0 8.62 9.0 9.5 10.0; do
  python3 agent/impl_runner.py combined_top $p >> /tmp/constraint_sweep.log 2>&1
  echo "=== TARGET $p DONE ===" >> /tmp/constraint_sweep.log
done
echo "=== ALL CONSTRAINT TARGETS DONE ===" >> /tmp/constraint_sweep.log
