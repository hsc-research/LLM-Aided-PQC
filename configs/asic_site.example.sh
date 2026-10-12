#!/usr/bin/env bash
# EXAMPLE ONLY. Replace values in a private site file; do not source unchanged.
# The project does not install EDA tools, PDKs, or compiled Synopsys libraries.
# Synopsys DC must receive valid licensed .db files, never renamed .lib files.
export ASAP7_LIB_DIR="/REPLACE_ME/approved/asap7/lib"
export ASAP7_DB_DIR="/REPLACE_ME/approved/asap7/db"
# Put your approved vendor installation on PATH outside this repository.
# Set these from your interface/library contract, then use the site Tcl template:
# export PQC_ASIC_INPUT_TRANSITION_NS="<reviewed nanoseconds>"
# export PQC_ASIC_CLOCK_UNCERTAINTY_NS="<reviewed nanoseconds>"
# export PQC_ASIC_OUTPUT_LOAD="<reviewed native-capacitance units>"
# Do not commit credentials, license-server details, or proprietary PDK files.
