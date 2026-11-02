    .section .text
    .globl _start

// T0 memory test image.
//
// The four lanes of the boot warp each walk a one and a zero through one line
// at a time; the walking bit advances with the line, and every eighth line gets
// the full 32-bit walk. The image occupies the first lines, so after testing
// the rest of the array the code copies itself to the last 4 KB (a region the
// walk just covered) and runs the copy. The copy tests the original image
// lines, which are no longer executing, so all 4096 lines are covered without
// overwriting the running image in place.
//
// The I-cache is not coherent with stores, so the finisher is copied to a line
// that was never fetched as code and the copy is fenced before the jump.

    .set ARRAY_BASE,  0x80000000
    .set ARRAY_END,   0x80040000
    .set FINISH_DEST, 0x8003F000
    .set NUM_LANES,   4

_start:
    // image_end is the first line the running image does not occupy.
    la      s2, image_end
    // Test everything from the image's end to the top of the array.
    mv      a0, s2
    li      a2, ARRAY_END
    li      a3, NUM_LANES * 64
    csrr    t0, 0xcc0               // lane (thread) id
    slli    t0, t0, 6
    add     a0, a0, t0
    jal     ra, walk_range
    mv      s0, a0                  // accumulated mismatches
    mv      s1, a1                  // last failing address

    // Copy the whole image to the last 4 KB, which the walk just covered.
    la      t0, _start
    la      t1, image_end
    li      t2, FINISH_DEST
1:  lw      t3, 0(t0)
    sw      t3, 0(t2)
    addi    t0, t0, 4
    addi    t2, t2, 4
    blt     t0, t1, 1b
    // T0's D-cache is write-through; fence the copy before entering it.
    fence

    // Enter the copy at the finisher's offset.
    la      t0, finish_start
    la      t1, _start
    sub     t0, t0, t1
    li      t1, FINISH_DEST
    add     t0, t0, t1
    mv      a1, s2                  // image_end: end of the lines to test now
    jr      t0

// Walks every line in [a0, a2) with stride a3, writing a line marker first and
// then a walking one and zero over word 0. The bit position is the line index
// modulo 32; every eighth line also gets a full 32-bit walk. Returns the
// mismatch count in a0 and the last failing address in a1.
walk_range:
    li      a4, 0                   // mismatches
    li      a5, 0                   // last failing address
    li      t6, ARRAY_BASE
    mv      a6, a0

    // Pass 1: a value unique to each line.
2:  bgeu    a6, a2, 3f
    sub     t0, a6, t6
    srli    t0, t0, 6
    li      t1, 0x4c000000
    or      t1, t1, t0
    sw      t1, 0(a6)
    add     a6, a6, a3
    j       2b

    // Pass 2: verify the marker, walk one bit per line (the bit position
    // advances with the line), and run the full 32-bit walk on every eighth
    // line.
3:  mv      a6, a0
4:  bgeu    a6, a2, 20f
    lw      t0, 0(a6)
    sub     t1, a6, t6
    srli    t1, t1, 6
    li      t2, 0x4c000000
    or      t2, t2, t1
    beq     t0, t2, 5f
    addi    a4, a4, 1
    mv      a5, a6
5:  li      t2, 1
    andi    t5, t1, 31
    sll     t2, t2, t5
    sw      t2, 0(a6)
    lw      t4, 0(a6)
    beq     t4, t2, 6f
    addi    a4, a4, 1
    mv      a5, a6
6:  not     t5, t2
    sw      t5, 0(a6)
    lw      t4, 0(a6)
    beq     t4, t5, 7f
    addi    a4, a4, 1
    mv      a5, a6
7:  andi    t5, t1, 7
    bnez    t5, 19f
    li      t3, 1
8:  sw      t3, 0(a6)
    lw      t4, 0(a6)
    beq     t4, t3, 9f
    addi    a4, a4, 1
    mv      a5, a6
9:  not     t5, t3
    sw      t5, 0(a6)
    lw      t4, 0(a6)
    beq     t4, t5, 10f
    addi    a4, a4, 1
    mv      a5, a6
10: slli    t3, t3, 1
    bnez    t3, 8b
19: add     a6, a6, a3
    j       4b

20: mv      a0, a4
    mv      a1, a5
    ret

finish_start:
    // The original image lines are free now; test them from the copy.
    li      a0, ARRAY_BASE
    mv      a2, a1
    li      a3, NUM_LANES * 64
    csrr    t0, 0xcc0
    slli    t0, t0, 6
    add     a0, a0, t0
    jal     ra, walk_range
    add     s0, s0, a0
    beqz    a0, 1f
    mv      s1, a1
1:  fence

    // Result and status keep the boot-test contract; the signature is per lane
    // so one failing lane cannot be hidden by another's store.
    lui     t0, 0x80001
    li      t1, 0xc0de
    sw      t1, 0(t0)
    li      t2, 0x600d0000
    sw      t2, 4(t0)
    csrr    t3, 0xcc0
    slli    t3, t3, 2
    add     t0, t0, t3
    li      t4, 0x5a5a0000
    li      t5, 0xffff
    and     t5, s0, t5
    or      t4, t4, t5
    fence
    sw      t4, 8(t0)
    sw      s1, 24(t0)

2:  j       2b

    .balign 64
image_end:
