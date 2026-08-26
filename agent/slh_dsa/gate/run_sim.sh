#!/bin/bash
set -u
R=/mnt/c/PQC/slh-dsa/rtl
rm -rf xsim.dir 2>/dev/null
# Files that set `default_nettype none and never restore it are compiled LAST
# so the directive does not leak into SPHINCSLET sources, which rely on
# implicit nets. Same class as HQC F31: read configuration, not a source defect.
NETTYPE_FILES="$R/imports/fifo.v $(find $R/sphincslet/sha -name '*.v' | sort | tr '\n' ' ')"
MAIN_FILES=$(find $R -name "*.v" ! -name clog2.v ! -name setting.v ! -name fifo.v ! -path "*/sha/*" | sort | tr '\n' ' ')
xvlog --relax $R/imports/global_include/clog2.v $R/sphincslet/setting.v \
      $MAIN_FILES $NETTYPE_FILES \
      -i $R/sphincslet -i $R/imports/global_include -i $R/sphincslet/fsm \
      > xvlog.log 2>&1
echo "xvlog errors: $(grep -c '^ERROR' xvlog.log)"
xelab --relax tb -s tb_sim -debug off > xelab.log 2>&1
echo "xelab errors: $(grep -c '^ERROR' xelab.log)"
xsim tb_sim -R > sim.log 2>&1
echo "--- result ---"
grep -E "signature is|sig gen done|sig verification done" sim.log
if grep -q "The signature is not matched" sim.log; then echo "GATE: FAIL"; exit 1; fi
G=/mnt/c/PQC/slh-dsa/gate/golden/SIG_file0_128f_w.hex
P=../../../../TECS_v8.srcs/sources_1/imports/data_sha2/SIG_file0_128f_w.hex
if ! diff -q "$G" "$P" > /dev/null 2>&1; then
  echo "GATE: FAIL (signature differs from golden)"; exit 1
fi
echo "GATE: signature matches golden"
if grep -q "The signature is matched" sim.log; then echo "GATE: PASS"; exit 0; fi
echo "GATE: INCONCLUSIVE"; exit 2
