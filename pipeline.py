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

class PipelinedProcessor(CPU):
    def __init__(self,registers,memory, assembler):
        super().__init__(registers, memory, assembler) 
        self.statistics = {
            "instructions_count": 0,
            "load_count": 0,
            "store_count": 0
        }
    def fetch(self): 
        pass 
    def decode(self): 
        pass 
    def execute(self): 
        pass 
    def memory_access(self): 
        pass
    def write_back(self): 
        pass
    