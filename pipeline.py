from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from hardware.FetchBuffer import FetchBuffer
from software.Assembler import Assembler 
import re
import os

reg_size = 32 
mem_size = 4096
rob_buffer_size = 4
registers = RegisterFile()
memory = Memory(mem_size=mem_size)
assembler = Assembler() 

config = { 
    "rob_buffer_size": 4,
    "iq_buffer_size": 1000,
    "n_instruction_fetch_cycle": 8, 
    "n_instruction_decode_cycle": 8,
    "lsq_buffer_size": 4,
    "rs_buffer_size": 4,
    "n_gprs": 32,
    "mem_size": 4096,
    "register_file_params": {}  
}

class PipelinedProcessor(CPU):
    def __init__(self, config):
        super().__init__(config) 
        self.fb = FetchBuffer(size=config["iq_buffer_size"])

    def fetch(self): 
        if not self.program: 
            print("no instructions to fetch as there is no program")
            return
        else: 
            for i in range(self.config["n_instruction_fetch_cycle"]):
                if self.fb.is_full():
                    break
                instruction = self.program[self.pc]
                self.pc += 1
                self.fb.enqueue(instruction)
    
                self.statistics["instructions_count"] += 1
                opcode = instruction.opcode
                if opcode == "lw" or opcode == "li" or opcode == "la":
                    self.statistics["load_count"] += 1
                if opcode == "sw":
                    self.statistics["store_count"] += 1
                if opcode == "beq" or opcode == "bne" or opcode == "bge" or opcode == "bgt" or opcode == "ble" or opcode == "blt":
                    self.statistics["branch_count"] += 1

    def decode(self): 
        for i in range(self.config["n_instruction_decode_cycle"]): 
            if self.fb.is_empty():
                break
            instruction = self.fb.dequeue()
            opcode = instruction[0]

    def issue(self): 
        pass
    def execute(self): 
        pass 
    def memory_access(self): 
        pass
    def write_back(self): 
        pass
    def run(self, program): 
        self.program = self.assembler.assemble(program, self)
        while self.statistics["cycles"] < 1000: 
            self.statistics["cycles"] += 5
            instruction = self.fetch()


            # decoded = self.decode(instruction) 
            # intermediate = self.execute(decoded)
            # self.memory_access(intermediate)
            # self.write_back(intermediate)
            if self.pc >= len(self.program):
                break
        print("Number of instructions executed: ", self.statistics["instructions_count"])
        print("Number of cycles: ", self.statistics["cycles"])
        print("Instruction per cycle: ", self.statistics["instructions_count"]/self.statistics["cycles"])
        print("Cycles per instruction: ", self.statistics["cycles"]/self.statistics["instructions_count"])
        print("Number of stores executed: ", self.statistics["store_count"])
        print("Number of loads executed: ", self.statistics["load_count"])
    
if __name__ == "__main__": 
    cpu = PipelinedProcessor(config)
    cpu.run(os.path.join(os.getcwd(), "programs\\vec_addition.s"))
    print(cpu.iq)

    for instruction in cpu.iq: 
        print(instruction)