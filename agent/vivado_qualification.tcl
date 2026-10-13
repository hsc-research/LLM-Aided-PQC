# Fixed post-synthesis object/report producer. Never sourced from model output.
# Vivado 2022.2; the Python adapter sets pqc_path_count and writes the manifest.
# Hex UTF-8 fields avoid Tcl/JSON evaluation and preserve generated cell names.
proc pqc_emit {stream args} {
    set fields {}
    foreach value $args {
        binary scan [encoding convertto utf-8 $value] H* encoded
        lappend fields $encoded
    }
    puts $stream [join $fields "\t"]
}
proc pqc_optional {property object} {
    if {[lsearch -exact [list_property $object] $property] < 0} {return ""}
    return [get_property $property $object]
}
set pqc_f [open objects.tsv w]
fconfigure $pqc_f -encoding utf-8 -translation lf
pqc_emit $pqc_f meta schema vivado-object-audit-v1
pqc_emit $pqc_f meta tool_version [version -short]
pqc_emit $pqc_f meta tool_build [version]
pqc_emit $pqc_f meta part [get_property PART [current_design]]
pqc_emit $pqc_f meta top [get_property NAME [current_design]]
pqc_emit $pqc_f meta stage post_synth
pqc_emit $pqc_f meta mode out_of_context
pqc_emit $pqc_f meta effort default
pqc_emit $pqc_f meta seed not_applicable
set pqc_cells [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]
pqc_emit $pqc_f meta primitive_count [llength $pqc_cells]
foreach cell $pqc_cells {
    pqc_emit $pqc_f cell [get_property NAME $cell] [get_property REF_NAME $cell] \
        [get_property PRIMITIVE_TYPE $cell] [pqc_optional REF_TYPE $cell] \
        [pqc_optional PRIMITIVE_SUBGROUP $cell] [pqc_optional FILE_NAME $cell] \
        [pqc_optional LINE_NUMBER $cell]
    if {[regexp {^(RAM|ROM|SRL)} [get_property REF_NAME $cell]]} {
        foreach property [list_property $cell] {
            if {[regexp {^(WRITE_MODE|READ_WIDTH|WRITE_WIDTH|DO[AB]_REG|INIT|SRVAL|RAM_MODE|SIM_COLLISION_CHECK)} $property]} {
                pqc_emit $pqc_f memory_property [get_property NAME $cell] $property [get_property $property $cell]
            }
        }
    }
}
# REF_TYPE, primitive classification and REF_NAME are independently retained.
# A zero latch_loops result alone is never a latch-inventory check.
set pqc_latches [get_cells -hierarchical -filter {IS_PRIMITIVE == 1 && (PRIMITIVE_SUBGROUP == LATCH || REF_NAME =~ LD*)}]
pqc_emit $pqc_f meta latch_inventory_count [llength $pqc_latches]
foreach cell $pqc_latches {pqc_emit $pqc_f latch [get_property NAME $cell]}
set pqc_boxes [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
pqc_emit $pqc_f meta blackbox_count [llength $pqc_boxes]
foreach cell $pqc_boxes {pqc_emit $pqc_f blackbox [get_property NAME $cell]}
foreach clock [get_clocks] {
    pqc_emit $pqc_f clock [get_property NAME $clock] [get_property PERIOD $clock] \
        [get_property IS_GENERATED $clock] [get_property SOURCE_PINS $clock]
}
# Each port gets independently queried min and max timing. Zero paths are unknown,
# not vacuous evidence of coverage. Explicit false paths are reported separately.
foreach port [get_ports] {
    set direction [get_property DIRECTION $port]
    set clock_count [llength [get_clocks -of_objects $port]]
    pqc_emit $pqc_f port [get_property NAME $port] $direction $clock_count
    if {$clock_count == 0 && ($direction eq "IN" || $direction eq "OUT")} {
        foreach delay {max min} {
            if {$direction eq "IN"} {
                set paths [get_timing_paths -from $port -delay_type $delay -max_paths 1 -nworst 1]
                set ignored [get_timing_paths -from $port -delay_type $delay -max_paths 1 -nworst 1 -user_ignored]
            } else {
                set paths [get_timing_paths -to $port -delay_type $delay -max_paths 1 -nworst 1]
                set ignored [get_timing_paths -to $port -delay_type $delay -max_paths 1 -nworst 1 -user_ignored]
            }
            set slack ""
            if {[llength $paths] == 1} {set slack [get_property SLACK $paths]}
            pqc_emit $pqc_f port_timing [get_property NAME $port] $delay [llength $paths] $slack [llength $ignored]
        }
    }
}
# Run the specific structural DRCs, recording the exact queried rule names.
set pqc_checks [get_drc_checks {MDRV-1 LUTLP-1 INBB-3}]
if {[llength $pqc_checks] != 3} {error "Missing required structural DRC checks"}
report_drc -no_waivers -checks $pqc_checks -name pqc_structural -file structural_drc.rpt
foreach rule $pqc_checks {
    pqc_emit $pqc_f drc_check [get_property NAME $rule] [get_property IS_ENABLED $rule]
}
foreach violation [get_drc_violations -name pqc_structural] {
    pqc_emit $pqc_f drc_violation [get_property NAME $violation] [get_property SEVERITY $violation]
}
check_timing -verbose -file check_timing.rpt
report_clocks -file clocks.rpt
report_exceptions -coverage -file exceptions.rpt
write_xdc effective.xdc
report_timing_summary -delay_type min_max -report_unconstrained -file timing.rpt
set pqc_pf [open paths.rpt w]
fconfigure $pqc_pf -encoding utf-8 -translation lf
foreach kind {setup hold} {
    if {$kind eq "setup"} {set delay max} else {set delay min}
    set paths [get_timing_paths -delay_type $delay -max_paths $pqc_path_count -nworst 1]
    set index 0
    foreach path $paths {
        incr index
        set id "$kind-$index"
        puts $pqc_pf "PQC_PATH_BEGIN $id"
        puts $pqc_pf [report_timing -of_objects $path -path_type full_clock_expanded -input_pins -return_string]
        puts $pqc_pf "PQC_PATH_END $id"
        pqc_emit $pqc_f path $id $kind [get_property STARTPOINT_PIN $path] \
            [get_property ENDPOINT_PIN $path] [get_property SLACK $path]
        foreach point [get_property POINTS $path] {
            set pin [get_property PIN $point]
            if {$pin eq ""} {continue}
            if {[get_property CLASS $pin] ne "pin"} {continue}
            foreach cell [get_cells -of_objects $pin] {
                pqc_emit $pqc_f path_cell $id [get_property NAME $cell]
            }
        }
    }
}
close $pqc_pf
pqc_emit $pqc_f meta complete 1
close $pqc_f
