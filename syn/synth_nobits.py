import os, glob

src_file = '/tmp/synth_g100_tc_Vortex/project_nobits.v'
out_dir = '/tmp/synth_g100_tc_Vortex/reports'
lib_path = '/OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib'

os.makedirs(out_dir, exist_ok=True)

lines = []
lines.append('# Auto-generated Yosys synthesis script')
lines.append('verilog_defaults -add -sv')
lines.append(f'read_liberty -lib "{lib_path}"')
lines.append(f'read_verilog -defer "{src_file}"')
lines.append('hierarchy -check -top Vortex')
lines.append('proc; opt')
lines.append('fsm; opt')
lines.append('memory; opt')
lines.append('memory_map; opt')
lines.append('alumacc; wreduce; share; opt')
lines.append('techmap; opt')
lines.append(f'dfflibmap -liberty "{lib_path}"')
lines.append(f'abc -markgroups -D 1.25 -liberty "{lib_path}"')
lines.append(f'tee -o {out_dir}/stat.rpt stat -liberty "{lib_path}" -top Vortex -width -tech cmos')
lines.append(f'write_verilog -noattr -noexpr {out_dir}/mapped.v')
lines.append(f'write_json {out_dir}/netlist.json')

# Fix paths for Docker
ys_content = '\n'.join(lines).replace('/tmp/synth_g100_tc_Vortex', '/work')

with open('/tmp/synth_g100_tc_Vortex/synth_nobits.ys', 'w') as f:
    f.write(ys_content)
print(f"Wrote synth_nobits.ys ({len(lines)} commands)")
