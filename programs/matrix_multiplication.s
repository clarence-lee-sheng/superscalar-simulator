.section .data
A: .word 1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17
B: .word 1,2,3,4,5,6,7,8,5,9,10,11,12,13,14,15,1,2,3,4,5,6,7,8,5,9,10,11,12,13,14,15,1,2,3,4,5,6,7,8,5,9,10,11,12,13,14,15,1,2,3,4,5,6,7,8,5,9,10,11,12,13,14,15
C: .word 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0



.text
.global _start 

_start: 
    li t1, 0
    li t2, 0
    li t3, 0 
    # setting matrix A dimensions to i x k and matrix B dimensions to k x j while C dimensions are i x j
    # i 
    li s1, 8
    # j
    li s2, 8
    # k
    li s3, 8
    
    la s4, A
    la s5, B
    la s6, C 

loop1:
    bge t1, s1, done 
    li t2, 0
    j loop2 

loop2:
    bge t2, s2, endloop2
    li t3, 0 
    j loop3 

# A[s1, s3], B[s3, s2]
# i: t1, j: t2, k: t3 

loop3: 
    # t4 for A indexing, t5 for B indexing, t6 for C indexing 
    bge t3, s3, endloop3
    mul t4, t1, s1
    add s11, t3, s4
    add t4, t4, s11
    lw t4, 0(t4)

    mul t5, t3, s3 
    add s11, t2, s5 
    add t5, t5, s11 
    lw t5, 0(t5)

    mul s7, t4, t5

    mul t6, s1, t1 
    add s11, t2, s6 
    add t6, t6, s11

    lw s8, 0(t6)
    add s7, s8, s7
    sw s7, 0(t6)
  
    addi t3, t3, 1 
    j loop3 

endloop2: 
  addi t1, t1, 1
  j loop1
endloop3: 
  addi t2, t2, 1
  j loop2

done: 
  ecall 
