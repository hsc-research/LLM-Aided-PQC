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
# UG835 returns a scalar for one object (including an empty string); UG894
# guarantees ordered lists for multiple objects. Never parse a scalar as a list.
# Reject multi-object disagreement rather than padding/truncating audit columns.
proc pqc_column {property objects} {
    set count [llength $objects]
    if {$count == 0} {return {}}
    set values [get_property $property $objects]
    if {$count == 1} {return [list $values]}
    if {[llength $values] != $count} {
        error "Property result cardinality mismatch: $property"
    }
    return $values
}
proc pqc_progress {stream message} {
    flush $stream
    puts "PQC_COLLECTOR [clock seconds] $message"
    flush stdout
}
proc pqc_cell_batch {stream cells} {
    set count [llength $cells]
    if {$count == 0} {return}
    set names [pqc_column NAME $cells]
    set refs [pqc_column REF_NAME $cells]
    set primitives [pqc_column PRIMITIVE_TYPE $cells]
    foreach property {REF_TYPE PRIMITIVE_SUBGROUP FILE_NAME LINE_NUMBER} {
        set columns($property) [lrepeat $count ""]
    }
    set index 0
    foreach cell $cells ref $refs {
        # Availability is inspected once for every individual object. Do not
        # assume that equal REF_NAME/types imply equal instance properties.
        set properties [list_property $cell]
        foreach property {REF_TYPE PRIMITIVE_SUBGROUP FILE_NAME LINE_NUMBER} {
            if {[lsearch -exact $properties $property] >= 0} {
                lappend selected($property) $cell
                lappend indices($property) $index
            }
        }
        set memory_properties($index) {}
        if {[regexp {^(RAM|ROM|SRL)} $ref]} {
            foreach property $properties {
                if {[regexp {^(WRITE_MODE|READ_WIDTH|WRITE_WIDTH|DO[AB]_REG|INIT|SRVAL|RAM_MODE|SIM_COLLISION_CHECK)} $property]} {
                    lappend memory_properties($index) $property
                    lappend selected($property) $cell
                    lappend indices($property) $index
                }
            }
        }
        incr index
    }
    # Each query contains only objects actually advertising that property.
    # Missing optional properties keep the same empty-string representation.
    foreach property [array names selected] {
        if {![info exists columns($property)]} {
            set columns($property) [lrepeat $count ""]
        }
        set values [pqc_column $property $selected($property)]
        foreach index $indices($property) value $values {
            lset columns($property) $index $value
        }
    }
    set index 0
    foreach name $names ref $refs primitive $primitives {
        pqc_emit $stream cell $name $ref $primitive \
            [lindex $columns(REF_TYPE) $index] [lindex $columns(PRIMITIVE_SUBGROUP) $index] \
            [lindex $columns(FILE_NAME) $index] [lindex $columns(LINE_NUMBER) $index]
        foreach property $memory_properties($index) {
            pqc_emit $stream memory_property $name $property [lindex $columns($property) $index]
        }
        incr index
    }
}
proc pqc_collect_cells {stream cells} {
    set total [llength $cells]
    pqc_emit $stream meta primitive_count $total
    pqc_progress $stream "primitive inventory begin: total=$total"
    set batch {}; set completed 0
    foreach cell $cells {
        lappend batch $cell
        if {[llength $batch] == 256} {
            pqc_cell_batch $stream $batch
            incr completed [llength $batch]
            pqc_progress $stream "primitive inventory: $completed/$total"
            set batch {}
        }
    }
    if {[llength $batch] > 0} {
        pqc_cell_batch $stream $batch
        incr completed [llength $batch]
    }
    if {$completed != $total} {error "Primitive collection cardinality mismatch"}
    pqc_progress $stream "primitive inventory complete: $completed/$total"
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
pqc_progress $pqc_f "querying primitive collection"
set pqc_cells [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]
pqc_collect_cells $pqc_f $pqc_cells
pqc_progress $pqc_f "querying latch and blackbox inventories"
# REF_TYPE, primitive classification and REF_NAME are independently retained.
# A zero latch_loops result alone is never a latch-inventory check.
set pqc_latches [get_cells -hierarchical -filter {IS_PRIMITIVE == 1 && (PRIMITIVE_SUBGROUP == LATCH || REF_NAME =~ LD*)}]
pqc_emit $pqc_f meta latch_inventory_count [llength $pqc_latches]
foreach cell $pqc_latches {pqc_emit $pqc_f latch [get_property NAME $cell]}
set pqc_boxes [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
pqc_emit $pqc_f meta blackbox_count [llength $pqc_boxes]
foreach cell $pqc_boxes {pqc_emit $pqc_f blackbox [get_property NAME $cell]}
pqc_progress $pqc_f "querying clocks and port timing"
set pqc_clock_names {}
foreach clock [get_clocks] {
    lappend pqc_clock_names [get_property NAME $clock]
    pqc_emit $pqc_f clock [get_property NAME $clock] [get_property PERIOD $clock] \
        [get_property IS_GENERATED $clock] [get_property SOURCE_PINS $clock]
}
# Each port gets independently queried min and max timing. Zero paths are unknown,
# not vacuous evidence of coverage. Explicit false paths are reported separately.
foreach port [get_ports] {
    set direction [get_property DIRECTION $port]
    if {[get_property CLASS $port] ne "port"} {error "Invalid port object"}
    # No clock on a data port is expected. Suppress only this optional lookup's
    # no-match warning; global clocks and timing coverage remain independently audited.
    set port_clocks [get_clocks -quiet -of_objects $port]
    foreach port_clock $port_clocks {
        if {[lsearch -exact $pqc_clock_names [get_property NAME $port_clock]] < 0} {
            error "Port clock missing from global clock inventory"
        }
    }
    set clock_count [llength $port_clocks]
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
pqc_progress $pqc_f "running structural and timing reports"
set pqc_checks [get_drc_checks {MDRV-1 LUTLP-1 INBB-3}]
if {[llength $pqc_checks] != 3} {error "Missing required structural DRC checks"}
set pqc_check_names {}
foreach rule $pqc_checks {
    if {[get_property CLASS $rule] ne "drc_check"} {error "Invalid structural DRC object class"}
    set rule_name [get_property NAME $rule]
    if {![get_property IS_ENABLED $rule]} {error "Disabled required structural DRC check: $rule_name"}
    lappend pqc_check_names $rule_name
}
if {[lsort $pqc_check_names] ne [lsort {MDRV-1 LUTLP-1 INBB-3}]} {
    error "Incorrect required structural DRC check names"
}
# Pass validated plain names, never the string representation of opaque handles.
report_drc -no_waivers -checks $pqc_check_names -name pqc_structural -file structural_drc.rpt
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
pqc_progress $pqc_f "collecting critical paths"
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
        puts $pqc_pf [report_timing -of_objects $path -return_string]
        puts $pqc_pf "PQC_PATH_END $id"
        pqc_emit $pqc_f path $id $kind [get_property STARTPOINT_PIN $path] \
            [get_property ENDPOINT_PIN $path] [get_property SLACK $path]
        # Vivado exposes the datapath cell membership directly on timing_path.
        # Clock-network ownership is not inferred from endpoint names.
        foreach cell [get_cells -of_objects $path] {
            pqc_emit $pqc_f path_cell $id [get_property NAME $cell]
        }
    }
}
close $pqc_pf
pqc_emit $pqc_f meta complete 1
pqc_progress $pqc_f "complete"
close $pqc_f
