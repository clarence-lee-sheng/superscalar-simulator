.section .data
A: .word 1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17
B: .word 1,2,0,1
C: .word 0,0,0,0,0,0,0,0,0

.text
.global _start 

_start: 
    li t0, 0
    li t1, 0
    # setting matrix A dimensions to i x k and matrix B dimensions to k x j while C dimensions are i x j

    # matrix dimension 
    li s0, 8
    li s1, 8
    li s2, 2 
    la a0, A
    la a1, B
    la a2, C 

    lw s3, 0(a1)
    lw s4, 1(a1)
    lw s5, 2(a1)
    lw s6, 3(a1)

    # stride 
    li s7 1 

    # get iteration counts 
    div t2, s0, s7
    sub t2, t2, s2
    addi t2, t2, 1
    div t3, s1, s7
    sub t3, t3, s2
    addi t3, t3, 1

loop1:
    bge t0, t2, done 
    li t1, 0
    j loop2 

loop2:
    bge t1, t3, endloop2
    li s11, 0 
    mul t4, t0, s0 
    add t5, zero, a0 
    add t4, t4, t1
    add t4, t5, t4 
    
    lw t4, 0(t4)
    mul t4, t4, s3

    addi t5, t0, 1 
    mul t5, t5, s0 
    add s8, zero, a0 
    add t5, t5, t1 
    add t5, t5, s8
    lw t5, 0(t5)
    mul t5, t5, s5 

    add a4, t4, t5 

    mul t4, t0, s0 
    add t4, t4, t1
    add s8, zero, a0 
    addi s8, s8, 1 
    add t4, t4, s8  
    lw t4, 0(t4)
    mul t4, t4, s4

    addi t5, t0, 1 
    mul t5, t5, s0 
    add s8, zero, a0 
    addi s8, s8, 1 
    add t5, t5, s8 
    lw t5, 0(t5)
    mul t5, t5, s6

    add t6, t4, t5

    add s11, a4, t6 

    mul t4, t0, t2 
    add t4, t4, t1 
    add t4, t4, a2
    sw s11, 0(t4)
    
    addi t1, t1, 1
    j loop2

endloop2: 
  addi t0, t0, 1
  j loop1

done: 
  ecall 
