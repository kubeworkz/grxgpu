#!/usr/bin/env python3
"""Report the paths whose blob starts with a machine-binary magic number.

Reads `git cat-file --batch` output on stdin and the matching request list on
argv[1] (one path per line, in the order the requests were sent — the batch
command answers in that order). Used by check_tracked_artifacts.sh to sniff a
whole staged commit with one git process instead of one per file.

The parser is in Python because the record separator only follows the blob
content: a shell has to skip that content to stay aligned, and `read -N`
drops NUL bytes, which desynchronises on exactly the binaries being sought.
"""

import sys

MAGICS = (
    b"\x7fELF",          # ELF
    b"MZ",               # PE / COFF
    b"\xcf\xfa\xed\xfe",  # Mach-O 64-bit
    b"\xce\xfa\xed\xfe",  # Mach-O 32-bit
    b"\xfe\xed\xfa\xce",  # Mach-O 32-bit, byte-swapped
    b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit, byte-swapped
    b"\xca\xfe\xba\xbe",  # Mach-O universal
)


def main():
    with open(sys.argv[1], "rb") as request_list:
        paths = [line.rstrip(b"\n") for line in request_list if line.strip()]

    stream = sys.stdin.buffer
    hits = []
    index = 0

    while True:
        header = stream.readline()
        if not header:
            break
        header = header.rstrip(b"\n")
        fields = header.rsplit(b" ", 1)

        # Content follows only when the last field is a size. The other two
        # answers are `<name> missing` and `<name> submodule` for a gitlink,
        # neither of which carries a body.
        if len(fields) != 2 or not fields[1].isdigit():
            index += 1
            continue

        body = stream.read(int(fields[1]))
        stream.read(1)  # record terminator

        if index < len(paths) and body.startswith(MAGICS):
            hits.append(paths[index])
        index += 1

    sys.stdout.buffer.write(b"".join(path + b"\n" for path in hits))


if __name__ == "__main__":
    main()
