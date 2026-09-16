# GRX G100 OpenROAD Synthesis Script v4
# Uses sv_elaborate with file list for SystemVerilog support

# Read technology library
read_liberty /libs/Nangate45_typ.lib

# Elaborate design using slang-elab (supports $bits(), etc.)
puts "=== Elaborating design with slang ==="
sv_elaborate -top Vortex_axi -f /tmp/grxgpu_files.f

# Synthesize
puts "=== Synthesizing ==="
synthesize

# Print statistics
puts "=== Statistics ==="
stats

# Write gate-level netlist
write_verilog /out/grxgpu_g100_synthesized.v

puts "=== Done ==="
exit
