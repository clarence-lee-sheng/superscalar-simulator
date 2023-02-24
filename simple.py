from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from software.Assembler import Assembler 
import re

import os

reg_size = 32 
mem_size = 4096
registers = RegisterFile(reg_size=32)
memory = Memory(mem_size=mem_size)
assembler = Assembler() 

class Simple(CPU):
    def __init__(self,registers,memory, assembler):
        super().__init__(registers, memory, assembler) 
        self.statistics = {
            "instructions_count": 0,
            "load_count": 0,
            "store_count": 0
        }
    def fetch(self): 
        if not self.program: 
            print("no instructions to fetch as there is no program")
            return
        else: 
            instruction = self.program[self.pc]
            self.statistics["instructions_count"] += 1
            opcode = instruction[0]
            if opcode == "lw" or opcode == "li" or opcode == "la":
                self.statistics["load_count"] += 1
            if opcode == "sw":
                self.statistics["store_count"] += 1
            return instruction
    def decode(self, instruction): 
        instruction = instruction.copy()
        opcode = instruction[0]
        if opcode == "add": 
            instruction[2] = self.registers[instruction[2]]
            instruction[3] = self.registers[instruction[3]]
        if opcode == "li": 
            instruction[2] = int(instruction[2])
        if opcode == "lw":
            reg = re.search(r"(?<=\()(.*?)(?=\))", instruction[2]).group()
            offset = re.search(r".*(?=\()", instruction[2]).group()
            instruction[2] = self.registers[reg] + int(offset)
        if opcode == "sw":
            reg = re.search(r"(?<=\()(.*?)(?=\))", instruction[2]).group()
            offset = re.search(r".*(?=\()", instruction[2]).group()
            instruction[1] = self.registers[instruction[1]]
            instruction[2] = self.registers[reg] + int(offset)
        if opcode == "addi":
            instruction[2] = int(instruction[2])
        return instruction
    def execute(self, decoded): 
        intermediate = dict()
        opcode = decoded[0]

        if opcode == "add":
            intermediate["value"] = decoded[2] + decoded[3]
            intermediate["type"] = "register"
            intermediate["id"] = decoded[1]
        elif opcode == "li":
            intermediate["value"] = decoded[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded[1]
        elif opcode == "la": 
            intermediate["value"] = decoded[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded[1]
        elif opcode == "lw":
            intermediate["value"] = self.memory[decoded[2]]
            intermediate["type"] = "register"
            intermediate["id"] = decoded[1]
        elif opcode == "sw":
            print(decoded)
            intermediate["value"] = decoded[1]
            intermediate["type"] = "memory"
            intermediate["id"] = decoded[2]
        elif opcode == "addi":
            intermediate["value"] = self.registers[decoded[1]] + decoded[2]
            intermediate["type"] = "register"
            intermediate["id"] = decoded[1]
        elif opcode == "ecall":
            intermediate["value"] = None 
            intermediate["type"] = "sys"
            intermediate["id"] = None 
        elif opcode == "j": 
            intermediate["type"] = "pc"
            intermediate["value"] = decoded[1]
        elif opcode == "beq":
            if self.registers[decoded[1]] == self.registers[decoded[2]]:
                intermediate["type"] = "pc"
                intermediate["value"] = decoded[3]
            else:
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        else:
            print(opcode)
        return intermediate
    def memory_access(self, intermediate):
        if intermediate["type"] == "register":
            self.pc += 1
        elif intermediate["type"] == "memory":
            print(intermediate["id"])
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
        while True: 
            instruction = self.fetch()
            decoded = self.decode(instruction) 
            intermediate = self.execute(decoded)
            self.memory_access(intermediate)
            self.write_back(intermediate)
            if self.pc >= len(self.program):
                break
        print("Number of instructions executed: ", self.statistics["instructions_count"])
        print("Number of stores executed: ", self.statistics["store_count"])
        print("Number of loads executed: ", self.statistics["load_count"])

cpu = Simple(registers, memory, assembler)
cpu.run(os.path.join(os.getcwd(), "benchmark\\vec_addition.s"))
print(registers)
print(cpu.memory[:40])

