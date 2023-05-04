.section .data
a: .word 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
b: .word 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
c: .word 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0


.text
.global _start 

_start: 
    # test
    li s5, 0 
    li s1, 20
    la s2, a
    la s3, b
    la s4, c  
    
loop: 
    beq s5, s1, done 
    add t1, s2, s5
    add t2, s3, s5
    add t3, s4, s5
    lw t1, 0(t1)
    lw t2, 0(t2)
    add t4, t1, t2 
    sw t4, 0(t3) 
    addi s5, s5, 1
    j loop

done: 
    ecall 