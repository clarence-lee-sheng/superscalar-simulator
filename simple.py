from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from software.Assembler import Assembler 
from copy import deepcopy
import re
import os

config = { 
    "rob_buffer_size": 4,
    "iq_buffer_size": 4,
    "lsq_buffer_size": 4,
    "rs_buffer_size": 4,
    "n_gprs": 32,
    "mem_size": 4096,
    "register_file_params": {}
}


class Simple(CPU):
    def __init__(self,config):
        super().__init__(config) 
        # self.statistics = {
        #     "instructions_count": 0,
        #     "load_count": 0,
        #     "store_count": 0, 
        #     "cycles": 0 
        # }
    def fetch(self): 
        if not self.program: 
            print("no instructions to fetch as there is no program")
            return
        else: 
            instruction = self.program[self.pc]
            self.statistics["instructions_count"] += 1
            opcode = instruction.opcode
            if opcode == "lw" or opcode == "li" or opcode == "la":
                self.statistics["load_count"] += 1
            if opcode == "sw":
                self.statistics["store_count"] += 1
            return instruction
    def decode(self, instruction): 
        print(instruction)
        # print(self.registers.physical_registers)
        instruction = deepcopy(instruction)
        opcode = instruction.opcode
        operands = instruction.operands
        if opcode == "add": 
            instruction.operands[1] = self.registers[instruction.operands[1]]
            instruction.operands[2] = self.registers[instruction.operands[2]]
        if opcode == "sub": 
            instruction.operands[1] = self.registers[instruction.operands[1]]
            instruction.operands[2] = self.registers[instruction.operands[2]]
        if opcode == "mul":
            instruction.operands[1] = self.registers[instruction.operands[1]]
            instruction.operands[2] = self.registers[instruction.operands[2]]
        if opcode == "li": 
            instruction.operands[1] = int(instruction.operands[1])
        if opcode == "lw":
            reg = re.search(r"(?<=\()(.*?)(?=\))", instruction.operands[1]).group()
            offset = re.search(r".*(?=\()", instruction.operands[1]).group()
            instruction.operands[1] = self.registers[reg] + int(offset)
        if opcode == "remw": 
            instruction.operands[1] = self.registers[instruction.operands[1]]
        if opcode == "sw":
            reg = re.search(r"(?<=\()(.*?)(?=\))", instruction.operands[1]).group()
            offset = re.search(r".*(?=\()", instruction.operands[1]).group()
            instruction.operands[0] = self.registers[instruction.operands[0]]
            instruction.operands[1] = self.registers[reg] + int(offset)
        if opcode == "addi":
            instruction.operands[2] = int(instruction.operands[2])
        return instruction
    def execute(self, decoded): 
        intermediate = dict()
        opcode = decoded.opcode

        if opcode == "add":
            print(decoded.operands)
            intermediate["value"] = decoded.operands[1] + decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "sub":
            print(decoded.operands)
            intermediate["value"] = decoded.operands[1] - decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "mul": 
            intermediate["value"] = decoded.operands[1] * decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "remw":
            intermediate["value"] = decoded.operands[1] % decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "li":
            intermediate["value"] = decoded.operands[1]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "la": 
            intermediate["value"] = decoded.operands[1]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "lw":
            intermediate["value"] = self.memory[decoded.operands[1]]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "sw":
            intermediate["value"] = decoded.operands[0]
            intermediate["type"] = "memory"
            intermediate["id"] = decoded.operands[1]
        elif opcode == "addi":
            intermediate["value"] = self.registers[decoded.operands[1]] + decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "subi": 
            intermediate["value"] = self.registers[decoded.operands[1]] - decoded.operands[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        elif opcode == "div": 
            intermediate["value"] = self.registers[decoded.operands[1]] / self.registers[decoded.operands[2]]
            intermediate["type"] = "register"
            intermediate["id"] = decoded.operands[0]
        
        elif opcode == "ecall":
            intermediate["value"] = None 
            intermediate["type"] = "sys"
            intermediate["id"] = None 
        elif opcode == "exit":
            intermediate["value"] = None 
            intermediate["type"] = "sys"
            intermediate["id"] = None 
        elif opcode == "j": 
            intermediate["type"] = "pc"
            intermediate["value"] = decoded.operands[0]
        elif opcode == "beq":
            if self.registers[decoded.operands[0]] == self.registers[decoded.operands[1]]:
                intermediate["type"] = "pc"
                intermediate["value"] = decoded.operands[2]
            else:
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        elif opcode == "bne":
            print("BNE", self.registers[decoded.operands[0]], self.registers[decoded.operands[1]])
            if self.registers[decoded.operands[0]] != self.registers[decoded.operands[1]]:
                intermediate["type"] = "pc"
                intermediate["value"] = decoded.operands[2]

            else:
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        elif opcode == "bge": 
            if self.registers[decoded.operands[0]] >= self.registers[decoded.operands[1]]:
                intermediate["type"] = "pc"
                intermediate["value"] = decoded.operands[2]
            else: 
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        elif opcode == "blt": 
            if self.registers[decoded.operands[0]] < self.registers[decoded.operands[1]]:
                intermediate["type"] = "pc"
                intermediate["value"] = decoded.operands[2]
            else: 
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        else:
            print(opcode)
        return intermediate
    def memory_access(self, intermediate):
        print(intermediate)
        if intermediate["type"] == "register":
            self.pc += 1
        elif intermediate["type"] == "memory":
            print(intermediate["id"])
            intermediate["id"] = int(intermediate["id"])
            self.memory[intermediate["id"]] = intermediate["value"]
            self.pc += 1
        elif intermediate["type"] == "sys":
            self.pc += 1 
        elif intermediate["type"] == "pc":
            self.pc = intermediate["value"]
        pass 
    def write_back(self, intermediate):
        if intermediate["type"] == "register":
            self.registers[intermediate["id"]] = intermediate["value"]
        elif intermediate["type"] == "memory":
            pass
        elif intermediate["type"] == "sys":
            pass
        elif intermediate["type"] == "pc":
            pass
        pass
    def run(self, program): 
        self.program = self.assembler.assemble(program, self)
        # for instruction in self.program: 
        #     print(instruction)
        # print(self.program)
        while True: 
            
            instruction = self.fetch()
            decoded = self.decode(instruction) 
            intermediate = self.execute(decoded)
            self.memory_access(intermediate)
            self.write_back(intermediate)
            self.statistics["cycles"] += 4 + instruction.cycles_to_execute
            print(instruction.cycles_to_execute)
            if self.pc >= len(self.program):
                break
        print("Number of instructions executed: ", self.statistics["instructions_count"])
        print("Number of cycles: ", self.statistics["cycles"])
        print("Instruction per cycle: ", self.statistics["instructions_count"]/self.statistics["cycles"])
        print("Cycles per instruction: ", self.statistics["cycles"]/self.statistics["instructions_count"])
        print("Number of stores executed: ", self.statistics["store_count"])
        print("Number of loads executed: ", self.statistics["load_count"])

cpu = Simple(config)
# cpu.run(os.path.join(os.getcwd(), "programs\\odd_counts.s"))
# cpu.run(os.path.join(os.getcwd(), "programs\\vec_addition.s"))
# cpu.run(os.path.join(os.getcwd(), "programs\\matrix_multiplication.s"))
cpu.run(os.path.join(os.getcwd(), "programs\\convolution.s"))
print(cpu.registers)
print(cpu.memory[:400])

