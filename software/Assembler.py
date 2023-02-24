import re
from .Instruction import Instruction

class Assembler(): 
    def __init__(self): 
        pass 
    def assemble(self, assembly_filename, cpu): 
        registers = cpu.registers 
        memory = cpu.memory 
        pc = cpu.pc

        program_file = open(assembly_filename, "r")
        mem_pointer = 0 
        memory_locations = {}        
        mode = "None"
        flag = False
        # print(program_file.readlines())

        instruction_pointer = 0
        start_function = ""
        call = ""
        
        instr_line = 0
        labels = {
        }
        for line in program_file.readlines(): 
            if not line.strip(): 
                continue 
            instruction = []
            if ".text" in line: 
                flag = True 
                continue 
            if ".global" in line: 
                start_function = line.split()[1]
                continue 
            if not flag: 
                continue 
            match = re.search(r"\w+(?=:)", line)
            if match: 
                matched = match.group()
                labels[matched] = instr_line 
                continue
            instr_line += 1 

        program = []

        program_file = open(assembly_filename, "r")

        for line in program_file.readlines(): 
            if not line.strip():
                continue
            if ".data" in line: 
                mode = "data"
                continue 
            if ".text" in line: 
                mode = "start"
                continue 

            if mode == "data": 
                line = line.strip()
                if line == "":
                    continue
                var = line.split(":")
                var_name = var[0]
                data_value = var[1].strip()
                type, data = data_value.split()
                if type == ".word": 
                    data = data.split(",")
                    memory_locations[var_name] = mem_pointer 
                    for d in data:
                        memory[mem_pointer] = int(d)
                        mem_pointer += 1 
            if mode == "start" and not line[0] == ".":
                match = re.search(r"\w+(?=:)", line)
                if match:
                    continue 
            # print("parse")
                instruction = self.parse_instruction(line, labels, memory_locations)
                program.append(instruction)
            # print(program)

        registers["gp"] = labels[start_function]      
        return(program)

    def parse_instruction(self, line, labels, memory_locations): 
        
        line = line.strip()
        line = line.replace(",", "").split()
        opcode = line[0]

        if opcode == "la": 
            line[2] = memory_locations[line[2]]
        elif opcode == "ecall": 
            pass 
        elif opcode == "beq" or opcode == "bne" or opcode == "blt" or opcode == "bge":
            line[3] = labels[line[3]]   
        elif opcode == "jal" or opcode == "j":
            line[1] = labels[line[1]]     
        return line 
