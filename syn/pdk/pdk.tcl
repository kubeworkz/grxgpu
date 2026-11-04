# PDK descriptor loader for the syn/ flows.
#
# A descriptor is a KEY=VALUE file in this directory; flow scripts read every
# technology-specific value (libraries, cell names, layers) from it so no cell
# or layer name is hardcoded in a script. Select one with PDK=<name>;
# sky130hd is the default. Field set: README.md.

set ::pdk_dir [file dirname [file normalize [info script]]]

proc pdk_load {{name ""}} {
    global PDK
    if {$name eq ""} {
        set name "sky130hd"
        if {[info exists ::env(PDK)] && $::env(PDK) ne ""} {
            set name $::env(PDK)
        }
    }
    set path [file join $::pdk_dir "${name}.pdk"]
    if {![file readable $path]} {
        error "no PDK descriptor '$name' (looked for $path)"
    }
    array unset PDK
    set PDK(PDK_FILE) $path
    set fh [open $path r]
    set lineno 0
    while {[gets $fh line] >= 0} {
        incr lineno
        set line [string trim $line]
        if {$line eq "" || [string index $line 0] eq "#"} {
            continue
        }
        set eq [string first "=" $line]
        if {$eq < 1} {
            close $fh
            error "$path:$lineno: expected KEY=VALUE, got '$line'"
        }
        set key [string trim [string range $line 0 [expr {$eq - 1}]]]
        set val [string trim [string range $line [expr {$eq + 1}] end]]
        if {[string length $val] >= 2
                && [string index $val 0] eq {"}
                && [string index $val end] eq {"}} {
            set val [string range $val 1 end-1]
        }
        set PDK($key) $val
    }
    close $fh
    pdk_require PDK_NAME PDK_NODE_NM PDK_READY PDK_LIBERTY PDK_TECH_LEF PDK_CELL_LEF
    if {$PDK(PDK_READY) ne "1"} {
        error "PDK $PDK(PDK_NAME) is marked PDK_READY=$PDK(PDK_READY) in $path: the descriptor is a skeleton, so set PDK_READY=1 only once its fields are the ones the flows should map against"
    }
    puts "PDK: $PDK(PDK_NAME), $PDK(PDK_NODE_NM) nm ($path)"
    return $name
}

proc pdk {key} {
    global PDK
    if {![info exists PDK($key)]} {
        error "PDK descriptor $PDK(PDK_FILE) has no $key"
    }
    return $PDK($key)
}

proc pdk_require {args} {
    global PDK
    set missing {}
    foreach key $args {
        if {![info exists PDK($key)] || $PDK($key) eq ""} {
            lappend missing $key
        }
    }
    if {[llength $missing] != 0} {
        error "PDK descriptor $PDK(PDK_FILE) is missing: [join $missing {, }]"
    }
}

proc pdk_lefs {} {
    set lefs {}
    foreach key {PDK_TECH_LEF PDK_CELL_LEF} {
        set lef [pdk $key]
        if {$lef ne ""} {
            lappend lefs $lef
        }
    }
    return $lefs
}

proc pdk_require_orram {} {
    if {[pdk PDK_HAS_ORRAM] ne "1"} {
        error "PDK [pdk PDK_NAME] cannot generate RAM macros (PDK_HAS_ORRAM=0 in [pdk PDK_FILE]); generate_ram needs standard-cell storage, tristate, inverter and tap cells"
    }
    pdk_require PDK_STORAGE_CELL PDK_TRISTATE_CELL PDK_INV_CELL PDK_TAP_CELL \
        PDK_FILLER_CELLS PDK_POWER_NET PDK_GROUND_NET PDK_MAX_TAP_DIST \
        PDK_ROUTING_LAYER PDK_VER_LAYER PDK_HOR_LAYER
}
