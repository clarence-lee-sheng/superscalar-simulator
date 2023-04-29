.section .data
result: .word 0 

.text
.global _start 

_start: 
    # test
    li s5, 0 
    li s1, 50
    li s2, 0 
    la s3, result
    
loop: 
    beq s5, s1, done 
    remw t1, s5, 2 
    bne t1, zero, add_count
    addi s5, s5, 1
    j loop

add_count: 
    addi s2, s2, 1
    sw s2, 0(s3)
    addi s5, s5, 1
    j loop 

done: 
    ecall 