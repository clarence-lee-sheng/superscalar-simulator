from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from hardware.Buffer import FetchBuffer, DecodeBuffer
from hardware.ReorderBuffer import ReorderBuffer, ReorderBufferEntry
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
    "decode_buffer_size": 100,
    "reorder_buffer_size": 128,
    "n_instruction_fetch_cycle": 8, 
    "n_instruction_decode_cycle": 8,
    "lsq_buffer_size": 4,
    "rs_buffer_size": 4,
    "n_gprs": 32,
    "mem_size": 4096,
    "register_file_params": {
        "n_physical_registers": 128,
    }, 
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
class FetchUnit: 
    def __init__(self, fetch_buffer, n_instruction_fetch_cycle): 
        self.fetch_buffer = fetch_buffer
        self.n_instruction_fetch_cycle = n_instruction_fetch_cycle
        self.pc = 0
    
    def cycle(self): 
        self.busy = True 
        if self.fetch_buffer.is_full():
            return
        self.busy = False
        
class DecodeUnit: 
    def __init__(self, decode_buffer, n_instruction_decode_cycle, reorder_buffer): 
        self.decode_buffer = decode_buffer
        self.reorder_buffer = reorder_buffer
        self.n_instruction_decode_cycle = n_instruction_decode_cycle
        self.busy = False 

    def cycle(self): 
        self.busy = True 
        if self.decode_buffer.is_full():
            return
        self.busy = False 

class BranchUnit: 
    def __init__(self): 
        self.branch_instruction = None 
        self.cycles_executed = 0
        self.busy = False
    def allocate(self, branch_instruction): 
        self.busy = True
        self.branch_instruction = branch_instruction
    def deallocate(self, result): 
        self.busy = False
        self.cycles_executed = 0
        return result
    def cycle(self): 
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.branch_instruction.n_cycles_to_execute:
            return 
        intermediate = dict()
        opcode = self.branch_instruction.opcode

        if opcode == "j": 
            intermediate["type"] = "pc"
            intermediate["value"] = self.branch_instruction.operands[0]
        elif opcode == "beq":
            if self.registers[self.branch_instruction.src1] == self.registers[self.branch_instruction.src2]:
                intermediate["type"] = "pc"
                intermediate["value"] = self.branch_instruction.src3
            else:
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        elif opcode == "bge": 
            if self.registers[self.branch_instruction.src1] >= self.registers[self.branch_instruction.src2]:
                intermediate["type"] = "pc"
                intermediate["value"] = self.branch_instruction.src3
            else: 
                intermediate["type"] = "pc"
                intermediate["value"] = self.pc + 1
        
        self.busy = False

class ALU:
    def __init__(self): 
        self.decoded_instruction = None
        self.cycles_executed = 0
        self.busy = False
    def allocate(self, decoded_instruction): 
        self.busy = True
        self.decoded_instruction = decoded_instruction
    def deallocate(self, result): 
        self.busy = False
        self.cycles_executed = 0
        return result
    def cycle(self): 
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.decoded_instruction.n_cycles_to_execute:
            return 
        intermediate = dict()
        opcode = self.decoded_instruction.opcode

        if opcode == "add":
            intermediate["value"] = self.decoded_instruction.src1 + self.decoded_instruction.src2
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "mul": 
            intermediate["value"] = self.decoded_instruction.src1 * self.decoded_instruction.src2
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "li":
            intermediate["value"] = self.decoded_instruction.src1
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "la": 
            intermediate["value"] = self.decoded_instruction.src1
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "lw":
            intermediate["value"] = self.memory[self.decoded_instruction.src1]
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "sw":
            intermediate["value"] = self.decoded_instruction.dest
            intermediate["type"] = "memory"
            intermediate["id"] = self.decoded_instruction.src1
        elif opcode == "addi":
            intermediate["value"] = self.registers[self.decoded_instruction.src1] + self.decoded_instruction.src2
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "ecall":
            intermediate["value"] = None 
            intermediate["type"] = "sys"
            intermediate["id"] = None 

        self.deallocate(intermediate)

class LSU: 
    def __init__(self): 
        self.busy = False
        self.load_cycle_time = 2
        self.store_cycle_time = 2
        self.cycles_executed = 0
        self.decoded_instruction = None
    
    def allocate(self, decoded_instruction):
        self.busy = True
        self.decoded_instruction = decoded_instruction
    
    def deallocate(self, result):
        self.busy = False
        self.cycles_executed = 0
        return result
    
    def cycle(self): 
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.load_cycle_time:
            return 
        intermediate = dict()
        opcode = self.decoded_instruction.opcode
        if opcode == "lw":
            intermediate["value"] = self.memory[self.decoded_instruction.src1]
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "sw":
            intermediate["value"] = self.decoded_instruction.dest
            intermediate["type"] = "memory"
            intermediate["id"] = self.decoded_instruction.src1
        self.deallocate(intermediate)

class DispatchUnit: 
    def __init__(self, decode_buffer, alu_issue_queue, lsu_issue_queue, branch_issue_queue): 
        self.decode_buffer = decode_buffer
        self.alu_issue_queue = alu_issue_queue
        self.lsu_issue_queue = lsu_issue_queue
        self.branch_issue_queue = branch_issue_queue
        self.busy = False
    
    def cycle(self):
        self.busy = True
        if self.decode_buffer.is_empty():
            return
        
        for decoded_instruction in self.decode_buffer: 
            micro_op = decoded_instruction.micro_op
            if micro_op == "ALU":
                if self.alu_issue_queue.is_full():
                    continue
                self.alu_issue_queue.enqueue(decoded_instruction)
            elif micro_op == "LSU":
                if self.lsu_issue_queue.is_full():
                    continue
                self.lsu_issue_queue.enqueue(decoded_instruction)
            elif micro_op == "BRANCH":
                if self.branch_issue_queue.is_full():
                    continue
                self.branch_issue_queue.enqueue(decoded_instruction)
        self.busy = False

class IssueUnit: 
    def __init__(self, issue_queue): 
        self.issue_queue = issue_queue
        self.busy = False
    
    def cycle(self): 
        self.busy = True
        if self.issue_queue.is_full():
            return
        self.busy = False
       
class PipelinedProcessor(CPU):
    def __init__(self, config):
        super().__init__(config) 
        self.fetch_buffer = FetchBuffer(size=config["fetch_buffer_size"])
        self.decode_buffer = DecodeBuffer(size=config["decode_buffer_size"])
        self.reorder_buffer = ReorderBuffer(reorder_buffer_size=config["reorder_buffer_size"],register_file=self.registers)
        self.branch_target_buffer = {}
        self.branch_history_buffer = {}
        self.branch_predictor = BranchPredictor(type=config["branch_predictor_type"])
        self.branch_instructions = ["beq", "bne", "blt", "bge"]
        self.jump_instructions = ["j", "jr", "jal", "jalr", "ret"]
        self.alu_instructions = ["add", "sub", "mul", "div", "addi", "subi", "muli", "divi"]
        self.load_store_instructions = ["lw", "sw", "li", "la"]
        print(self.registers)

        self.FetchUnit = FetchUnit(self.fetch_buffer, config["n_instruction_fetch_cycle"])
        self.DecodeUnit = DecodeUnit(self.decode_buffer, self.reorder_buffer, config["n_instruction_decode_cycle"])
        # self.ExecuteUnit = [ExecuteUnit(self.execute_buffer, config["n_instruction_execute_cycle"])]

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
            stale_physical_register = None 
            if instruction.dest:
                instruction.dest, stale_physical_register = self.registers.rename(instruction.dest, type ="dest")
            if instruction.src1: 
                instruction.src1 = self.registers.rename(instruction.src1, type="src")
            if instruction.src2: 
                instruction.src2 = self.registers.rename(instruction.src2, type="src")
            if instruction.src3:
                instruction.src3 = self.registers.rename(instruction.src3, type="src")
            return instruction, stale_physical_register
        
        print(self.config["n_instruction_decode_cycle"])
        for i in range(self.config["n_instruction_decode_cycle"]): 
            print(self.decode_buffer.is_full(),self.reorder_buffer.is_full() , not self.registers.RAT.has_free())
            if self.decode_buffer.is_full() or self.reorder_buffer.is_full() or not self.registers.RAT.has_free(): 
                print("decode stalling")
                break
            if self.fetch_buffer.is_empty():
                break
            instruction = self.fetch_buffer.dequeue()
            opcode = instruction.opcode
            operands = instruction.operands
            if opcode not in self.branch_instructions and opcode not in self.jump_instructions: 
                dest = operands[0]
                src1 = operands[1] if len(operands) >= 2 else None 
                src2 = operands[2] if len(operands) >= 3 else None 
                src3 = operands[3] if len(operands) >= 4 else None
                decoded_instruction = DecodedInstruction(instruction=instruction, dest=dest, src1=src1, src2=src2, src3=src3)
            else: 
                dest = None 
                src1 = operands[0] if len(operands) >= 1 else None
                src2 = operands[1] if len(operands) >= 2 else None
                src3 = operands[2] if len(operands) >= 3 else None
                decoded_instruction = DecodedInstruction(instruction=instruction, dest=dest, src1=src1, src2=src2, src3=src3)

            decoded_instruction, stale_physical_register = rename(decoded_instruction)
            if opcode in self.alu_instructions:
                decoded_instruction.micro_op = "ALU"
            elif opcode in self.load_store_instructions:
                decoded_instruction.micro_op = "LSU"
            elif opcode in self.branch_instructions or self.jump_instructions:
                # decoded_instruction.micro_op = "BRANCH UNIT"
                decoded_instruction.micro_op = "BRANCH"
            type = decoded_instruction.micro_op
            pc = decoded_instruction.pc
            dest = decoded_instruction.dest
            value = None 

            self.decode_buffer.enqueue(decoded_instruction)
            self.reorder_buffer.enqueue(pc, type, dest, value, stale_physical_register)

            #branch target for unconditionals is computed in decode stage
            #branch target for conditionals is computed in execute stage
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
    print(cpu.decode_buffer)
    print(cpu.reorder_buffer)
    print(cpu.registers.RAT.free)

    for instruction in cpu.decode_buffer: 
        print(instruction)