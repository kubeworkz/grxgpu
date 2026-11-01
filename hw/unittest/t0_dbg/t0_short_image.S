    .section .text
    .globl _start

// Minimal boot image for the JTAG restart and timeout-recovery checks: publish
// the expected result/status and the per-lane signature, then spin.
_start:
    lui     t0, 0x80001
    li      t1, 0xc0de
    sw      t1, 0(t0)
    li      t2, 0x600d0000
    sw      t2, 4(t0)
    csrr    t3, 0xcc0
    slli    t3, t3, 2
    add     t0, t0, t3
    li      t4, 0x5a5a0000
    sw      t4, 8(t0)
1:  j       1b

    .balign 64
image_end:
