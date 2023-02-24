
from abc import ABC, abstractmethod

class CPU(ABC):
    def __init__(self, registers, memory, assembler):
        self._registers = registers 
        self._memory = memory 
        self._pc = 0
        self._program = None 
        self._assembler = assembler
    
    @property
    def registers(self):
        return self._registers 

    @registers.setter
    def registers(self,value):
        self._registers = value 

    @property
    def memory(self):
        return self._memory 

    @memory.setter
    def memory(self,value):
        self._memory = value 

    @property
    def pc(self):
        return self._pc 

    @pc.setter
    def pc(self,value):
        self._pc = value 

    @property
    def assembler(self):
        return self._assembler 

    @assembler.setter
    def assembler(self,value):
        self._assembler = value 

    @property
    def program(self):
        return self._program 

    @program.setter
    def program(self,value):
        self._program = value 

    @abstractmethod 
    def fetch(self): 
        # instructions typically stored in memory and the processor fetches them as it executes the program 
        # managed by an instruction fetch unit 
        # instructions are typically stored in a small instruction cache and is typically organized as a set of three lines, each containing multiple instructions 
        # To fetch an instruction, it checks if the instruction is from the cache, if it is, read from the cache, else, fetch from memory
        pass 

    @abstractmethod
    def decode(self): 
        # it extracts the instruction fetched from the previous stage from the instruction register 
        # it is then passed to the instruction decoder, which is responsible for interpreting the opcode and operands of the instruction.
        # it reads the operands from registers and sends control signals for the execute stage to happen 
        pass 

    @abstractmethod 
    def execute(self): 
        # uses the ALU and shifter unit to perform the operations specified by the decode unit 
        pass 

    @abstractmethod 
    def memory_access(self): 
        # main function is to read data from memory 
        pass 

    @abstractmethod
    def write_back(self): 
        # main function is to write data back to memory 
        pass
 

