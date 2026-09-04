#!/usr/bin/env python3
"""Strip orphaned preprocessor directives from flattened SV."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/tcu_flat_v2.sv'
with open(path) as f:
    content = f.read()

lines = content.split('\n')
cleaned = [l for l in lines if not re.match(r'^\s*`(?:endif|ifdef|ifndef|else|elsif)', l)]
with open(path, 'w') as f:
    f.write('\n'.join(cleaned))

print("Stripped to %d lines" % len(cleaned))
