from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from hardware.Buffer import FetchBuffer, DecodeBuffer
from hardware.BranchPredictor import BranchPredictor
from software.Assembler import Assembler 
from software.Instruction import DecodedInstruction
import re
import os

# questions 
# Must instructions be dispatched to the issue queue in order 


reg_size = 32 
mem_size = 4096
rob_buffer_size = 4
registers = RegisterFile()
memory = Memory(mem_size=mem_size)
assembler = Assembler() 

config = { 
    "rob_buffer_size": 4,
    "fetch_buffer_size": 10,
    "decode_buffer_size": 1000,
    "n_instruction_fetch_cycle": 8, 
    "n_instruction_decode_cycle": 8,
    "lsq_buffer_size": 4,
    "rs_buffer_size": 4,
    "n_gprs": 32,
    "mem_size": 4096,
    "register_file_params": {}, 
    "branch_predictor_type": "static" 
}

# instruction queue 
# decode the instruction, rename and place them in the reorder buffer 
# put the decoded and renamed instructions into a decode buffer 
# issue the instructions from the decode buffer into the issue queue 
# dispatch the isntructions to execute once all inputs are satisfied 
# execute the instructions 
# broadcast the results to the corresponding tag associated with the physical register 
# writeback to memory 
# check if any registers can be committed 

# if branch, 


class PipelinedProcessor(CPU):
    def __init__(self, config):
        super().__init__(config) 
        self.fetch_buffer = FetchBuffer(size=config["fetch_buffer_size"])
        self.decode_buffer = DecodeBuffer(size=config["decode_buffer_size"])
        self.branch_predictor = BranchPredictor(type=config["branch_predictor_type"])
        self.branch_instructions = ["beq", "bne", "blt", "bge"]
        self.jump_instructions = ["j", "jr", "jal", "jalr", "ret"]
        self.alu_instructions = ["add", "sub", "mul", "div", "addi", "subi", "muli", "divi"]
        self.load_store_instructions = ["lw", "sw", "li", "la"]
        print(self.registers)

    def fetch(self): 
        if not self.program: 
            print("no instructions to fetch as there is no program")
            return
        else: 
            for i in range(self.config["n_instruction_fetch_cycle"]):
                if self.fetch_buffer.is_full():
                    break
                if self.pc >= len(self.program): 
                    break
                instruction = self.program[self.pc]
                self.fetch_buffer.enqueue(instruction)
    
                self.statistics["instructions_count"] += 1
                opcode = instruction.opcode
                if opcode == "lw" or opcode == "li" or opcode == "la":
                    self.statistics["load_count"] += 1
                if opcode == "sw":
                    self.statistics["store_count"] += 1
                if opcode == "beq" or opcode == "bne" or opcode == "bge" or opcode == "bgt" or opcode == "ble" or opcode == "blt":
                    self.statistics["branch_count"] += 1
                if opcode in ["beq", "bge", "bgt", "ble", "blt"]: 
                    branch_pc = instruction.operands[2]
                    to_branch = self.branch_predictor.predict(branch_pc, self.pc)
                    if to_branch: 
                        self.pc = branch_pc 
                    else: 
                        self.pc += 1 
                elif opcode in ["j"]: 
                    branch_pc = instruction.operands[0]
                    to_branch = self.branch_predictor.predict(branch_pc, self.pc)
                    if to_branch: 
                        self.pc = branch_pc 
                    else: 
                        self.pc += 1 

                else:     
                    self.pc += 1

    #rename the registers

    def decode(self): 
        # implement decode and rename 

        def rename(instruction): 
            if instruction.dest:
                instruction.dest = self.registers.RAT.table[instruction.dest] if instruction.dest in self.registers.RAT.table else instruction.dest
            if instruction.src1: 
                instruction.src1 = self.registers.RAT.table[instruction.src1] if instruction.src1 in self.registers.RAT.table else instruction.src1
            if instruction.src2: 
                instruction.src2 = self.registers.RAT.table[instruction.src2] if instruction.src2 in self.registers.RAT.table else instruction.src2
            if instruction.src3:
                instruction.src3 = self.registers.RAT.table[instruction.src3] if instruction.src3 in self.registers.RAT.table else instruction.src3
            return instruction
         
        for i in range(self.config["n_instruction_decode_cycle"]): 
            if self.decode_buffer.is_full(): 
                break
            if self.fetch_buffer.is_empty():
                break
            instruction = self.fetch_buffer.dequeue()
            opcode = instruction.opcode
            operands = instruction.operands
            if instruction not in self.branch_instructions and instruction not in self.jump_instructions: 
                dest = operands[0]
                src1 = operands[1] if len(operands) >= 2 else None 
                src2 = operands[2] if len(operands) >= 3 else None 
                src3 = operands[3] if len(operands) >= 4 else None
                decoded_instruction = DecodedInstruction(instruction=instruction, dest=dest, src1=src1, src2=src2, src3=src3)
                print(src1, src2, src3)
            else: 
                dest = None 
                src1 = operands[0] if len(operands) >= 1 else None
                src2 = operands[1] if len(operands) >= 2 else None
                src3 = operands[2] if len(operands) >= 3 else None
                decoded_instruction = DecodedInstruction(instruction=instruction, dest=dest, src1=src1, src2=src2, src3=src3)


            instruction = rename(decoded_instruction)
            print(instruction)

                # if len()
            if opcode in self.alu_instructions:
                instruction.micro_op = "ALU"
            elif opcode in self.load_store_instructions:
                instruction.micro_op = "LSU"
            elif opcode in self.branch_instructions or self.jump_instructions:
                instruction.micro_op = "BRANCH UNIT"
            
       

    def dispatch(self): 
        
        pass
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
            decoded = self.decode()
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
    print(cpu.fetch_buffer)

    for instruction in cpu.fetch_buffer: 
        print(instruction)