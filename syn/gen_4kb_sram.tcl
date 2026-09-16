read_liberty /OpenROAD/test/sky130hd/sky130_fd_sc_hd__tt_025C_1v80.lib
read_lef /OpenROAD/test/sky130hd/sky130hd.tlef
read_lef /OpenROAD/test/sky130hd/sky130_fd_sc_hd_merged.lef

puts "=== Generating 4KB SRAM (32-bit x 1024 words) ==="
set t0 [clock seconds]
generate_ram \
  -word_size 32 \
  -num_words 1024 \
  -rw_ports 1 \
  -column_mux_ratio 4 \
  -storage_cell sky130_fd_sc_hd__dfxtp_1 \
  -tristate_cell sky130_fd_sc_hd__ebufn_4 \
  -inv_cell sky130_fd_sc_hd__inv_1 \
  -power_net_name VDD \
  -ground_net_name VSS \
  -routing_layer {met1 0.48} \
  -ver_layer {met2 0.48 40} \
  -hor_layer {met3 0.48 20} \
  -filler_cells {sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8} \
  -tapcell sky130_fd_sc_hd__tap_1 \
  -max_tap_dist 15
set t1 [clock seconds]
puts "=== RAM generated in [expr {$t1 - $t0}] seconds ==="

write_verilog /out/sram_32x1024.v
write_abstract_lef /out/sram_32x1024.lef
write_def /out/sram_32x1024.def
puts "=== All outputs written ==="
exit
