source [file join [file dirname [file normalize [info script]]] pdk pdk.tcl]

pdk_load
pdk_require_orram

read_liberty [pdk PDK_LIBERTY]
foreach lef [pdk_lefs] { read_lef $lef }

puts "=== Generating 4KB SRAM (32-bit x 1024 words) ==="
set t0 [clock seconds]
generate_ram \
  -word_size 32 \
  -num_words 1024 \
  -rw_ports 1 \
  -column_mux_ratio 4 \
  -storage_cell [pdk PDK_STORAGE_CELL] \
  -tristate_cell [pdk PDK_TRISTATE_CELL] \
  -inv_cell [pdk PDK_INV_CELL] \
  -power_net_name [pdk PDK_POWER_NET] \
  -ground_net_name [pdk PDK_GROUND_NET] \
  -routing_layer [pdk PDK_ROUTING_LAYER] \
  -ver_layer [pdk PDK_VER_LAYER] \
  -hor_layer [pdk PDK_HOR_LAYER] \
  -filler_cells [pdk PDK_FILLER_CELLS] \
  -tapcell [pdk PDK_TAP_CELL] \
  -max_tap_dist [pdk PDK_MAX_TAP_DIST]
set t1 [clock seconds]
puts "=== RAM generated in [expr {$t1 - $t0}] seconds ==="

write_verilog /out/sram_32x1024.v
write_abstract_lef /out/sram_32x1024.lef
write_def /out/sram_32x1024.def
puts "=== All outputs written ==="
exit
