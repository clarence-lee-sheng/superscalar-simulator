.section .data
a: .word 1,2,3,4,5,6,7,8,9,10 
b: .word 1,2,3,4,5,6,7,8,9,10
c: .word 0,0,0,0,0,0,0,0,0,0 


.text
.global _start 

_start: 
    li s0, 0 
    li s1, 10
    la s2, a
    la s3, b
    la s4, c  
    
loop: 
    beq s0, s1, done 
    add t1, s2, s0
    add t2, s3, s0
    add t3, s4, s0
    lw t1, 0(t1)
    lw t2, 0(t2)
    add t4, t1, t2 
    sw t4, 0(t3) 
    addi s0, s0, 1
    j loop

done: 
    ecall 