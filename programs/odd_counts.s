.section .data
result: .word 0 

.text
.global _start 

_start: 
    # test
    li s5, 0 
    li s1, 400
    li s2, 0 
    li s4, 1.0
    la s3, result
    
loop: 
    beq s5, s1, done 
    remw t1, s5, 2
    beq, t1, s4, add_count
    add s5, s5, s4
    j loop

add_count: 
    addi s2, s2, 1
    sw s2, 0(s3)
    add s5, s5, s4
    j loop 

done: 
    ecall 