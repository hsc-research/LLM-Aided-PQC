# Copy this file for your machine and point tools.<tool>.setup_tcl at the copy.
# These variables are intentionally required: no technology-independent load,
# slew, or uncertainty number can be assumed for a defensible PPA comparison.
# Set all three environment variables to reviewed numeric values before a run.
foreach name {PQC_ASIC_INPUT_TRANSITION_NS PQC_ASIC_CLOCK_UNCERTAINTY_NS PQC_ASIC_OUTPUT_LOAD} {
    if {![info exists env($name)] || ![string is double -strict $env($name)] || $env($name) <= 0} {
        error "Set $name to a reviewed positive finite site value"
    }
    if {$env($name) == Inf || $env($name) == -Inf} { error "Non-finite site value: $name" }
}
# The driver defines PQC_PERIOD in the declared native library time unit.
set PQC_INPUT_TRANSITION [expr {$env(PQC_ASIC_INPUT_TRANSITION_NS) * $PQC_PERIOD / $PQC_PERIOD_NS}]
set PQC_CLOCK_UNCERTAINTY [expr {$env(PQC_ASIC_CLOCK_UNCERTAINTY_NS) * $PQC_PERIOD / $PQC_PERIOD_NS}]
set PQC_OUTPUT_LOAD $env(PQC_ASIC_OUTPUT_LOAD)
if {$PQC_CLOCK_UNCERTAINTY >= $PQC_PERIOD} { error "Clock uncertainty must be less than period" }
# PQC_OUTPUT_LOAD uses the tool's native capacitance unit, not necessarily pF.
# Check loaded libraries and DC units.rpt; keep baseline/candidate identical.
# Add only reviewed site setup below. Do not change clock/time units here.
# No licensed PDK, library bytes, credentials, or license-server settings belong
# in this public template. Keep licensed files outside the checkout.
