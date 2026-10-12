# Local data-only source manifest adapter. No EDA tool is launched here.
# Source this file from a Vivado, DC, or Genus site-qualified script.
set abr_root [file normalize [file join [file dirname [info script]] ..]]
set abr_top abr_unified_top
set abr_sources [list]
set abr_include_dirs [list]
set abr_generic_synthesis_defines [list SYNTHESIS]
set abr_fpga_synthesis_defines [list SYNTHESIS RV_FPGA_OPTIMIZE]
set abr_fh [open [file join $abr_root integration sources.f] r]
set abr_filelist [read $abr_fh]
close $abr_fh
foreach abr_line [split $abr_filelist "\n"] {
    set abr_line [string trim $abr_line]
    if {$abr_line eq "" || [string match "#*" $abr_line]} { continue }
    if {[string first "+incdir+" $abr_line] == 0} {
        set abr_path [file normalize [file join $abr_root [string range $abr_line 8 end]]]
        if {![file isdirectory $abr_path]} { error "Missing include directory: $abr_path" }
        lappend abr_include_dirs $abr_path
    } else {
        set abr_path [file normalize [file join $abr_root $abr_line]]
        if {![file isfile $abr_path]} { error "Missing RTL source: $abr_path" }
        lappend abr_sources $abr_path
    }
}
unset abr_fh abr_filelist abr_line abr_path
