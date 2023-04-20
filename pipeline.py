from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from hardware.Buffer import FetchBuffer, DecodeBuffer
from hardware.ReorderBuffer import ReorderBuffer, ReorderBufferEntry
from hardware.BranchPredictor import BranchPredictor
from hardware.IssueQueue import IssueQueue, IssueSlot
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
    "mem_issue_queue_size": 32, 
    "alu_issue_queue_size": 32,
    "branch_issue_queue_size": 32,
    "n_instruction_fetch_cycle": 8, 
    "n_instruction_decode_cycle": 8,
    "lsq_buffer_size": 4,
    "rs_buffer_size": 4,
    "n_gprs": 32,
    "mem_size": 4096,
    "dispatch_width": 4,
    "register_file_params": {
        "n_physical_registers": 128,
    }, 
    "execution_units": {
        "n_alus": 3,
        "n_lsus": 2,
        "n_branch_units": 1
    },
    "branch_predictor_type": "static", 
    "instructions": {
        "branch_instructions": ["beq", "bne", "blt", "bge"],
        "jump_instructions": ["j", "jr", "jal", "jalr", "ret"],
        "alu_instructions": ["add", "sub", "mul", "div", "addi", "subi", "muli", "divi"],
        "load_store_instructions": ["lw", "sw", "li", "la"]
    }
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
    def __init__(self, fetch_buffer, n_instruction_fetch_cycle,branch_predictor, statistics={}, program=None): 
        self.program = program
        self.fetch_buffer = fetch_buffer
        self.n_instruction_fetch_cycle = n_instruction_fetch_cycle
        self.pc = 0
        self.statistics = statistics
        self.branch_predictor = branch_predictor
    
    def cycle(self): 
        self.busy = True 
        if self.fetch_buffer.is_full():
            return
        
        for i in range(self.n_instruction_fetch_cycle):
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

        self.busy = False
        
class DecodeUnit: 
    def __init__(self, fetch_buffer, decode_buffer, n_instruction_decode_cycle, reorder_buffer, register_file, instructions): 
        self.fetch_buffer = fetch_buffer
        self.decode_buffer = decode_buffer
        self.reorder_buffer = reorder_buffer
        self.n_instruction_decode_cycle = n_instruction_decode_cycle
        self.register_file = register_file
        self.busy = False 
        self.instructions = instructions

    def cycle(self): 
        self.busy = True 
        if self.decode_buffer.is_full():
            return
        
        def rename(instruction): 
            stale_physical_register = None 
            if instruction.dest:
                instruction.dest, stale_physical_register = self.register_file.rename(instruction.dest, type ="dest")
            if instruction.src1: 
                instruction.src1 = self.register_file.rename(instruction.src1, type="src")
            if instruction.src2: 
                instruction.src2 = self.register_file.rename(instruction.src2, type="src")
            if instruction.src3:
                instruction.src3 = self.register_file.rename(instruction.src3, type="src")
            return instruction, stale_physical_register
        
        # print(self.config["n_instruction_decode_cycle"])
        for i in range(self.n_instruction_decode_cycle): 
            # print(self.decode_buffer.is_full(),self.reorder_buffer.is_full() , not self.register_file.RAT.has_free())
            if self.decode_buffer.is_full() or self.reorder_buffer.is_full() or not self.register_file.RAT.has_free(): 
                # print("decode stalling")
                break
            if self.fetch_buffer.is_empty():
                break
            instruction = self.fetch_buffer.dequeue()
            opcode = instruction.opcode
            operands = instruction.operands
            if opcode not in self.instructions["branch_instructions"] and opcode not in self.instructions["jump_instructions"]: 
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
            if opcode in self.instructions["alu_instructions"]:
                decoded_instruction.micro_op = "ALU"
            elif opcode in self.instructions["load_store_instructions"]:
                decoded_instruction.micro_op = "LSU"
            elif opcode in self.instructions["branch_instructions"] or self.instructions["jump_instructions"]:
                # decoded_instruction.micro_op = "BRANCH UNIT"
                decoded_instruction.micro_op = "BRANCH"
            type = decoded_instruction.micro_op
            pc = decoded_instruction.pc
            dest = decoded_instruction.dest
            value = None 

            self.decode_buffer.enqueue(decoded_instruction)
            self.reorder_buffer.enqueue(pc, type, dest, value, stale_physical_register)
        self.busy = False 

class BranchUnit: 
    def __init__(self, bypass_network): 
        self.branch_instruction = None 
        self.cycles_executed = 0
        self.busy = False
        self.bypass_network = bypass_network
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
    def __init__(self, bypass_network): 
        self.decoded_instruction = None
        self.cycles_executed = 0
        self.busy = False
        self.bypass_network = bypass_network

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


# Address generation unit 
# 1. instruction come in 
# 2. read the operands and compute the address 

class AGU: 
    def __init__(self, memory, bypass_network): 
        self.busy = False
        self.cycle_time = 1 
        self.cycles_executed = 0
        self.decoded_instruction = None
        self.memory = memory
        self.bypass_network = bypass_network
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
        if self.cycles_executed < self.cycle_time:
            return 
        intermediate = dict()
        opcode = self.decoded_instruction.opcode
        if opcode == "li": 
            intermediate["value"] = self.decoded_instruction.src1
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        if opcode == "lw":
            # compute the address
            
            intermediate["value"] = self.decoded_instruction.src1 + self.decoded_instruction.src2
            intermediate["type"] = "memory"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "sw":
            # compute the address
            intermediate["value"] = self.decoded_instruction.src1 + self.decoded_instruction.src2
            intermediate["type"] = "memory"
            intermediate["id"] = self.decoded_instruction.dest
        else: 
            raise Exception("Invalid opcode for AGU", opcode)
        self.deallocate(intermediate)

class LSU_entry: 
    def __init__(self, pc, valid, addr, data): 
        self.dest = None
        self.valid = valid
        self.addr = addr
        self.data = data
        self.pc = pc
    def __str__(self) -> str:
        return f"pc: {self.pc}, valid: {self.valid}, addr: {self.addr}, data: {self.data}"
        pass
    

class LSU: 
    def __init__(self, memory, bypass_network): 
        self.busy = False
        self.load_cycle_time = 2
        self.store_cycle_time = 2
        self.cycles_executed = 0
        self.decoded_instruction = None
        self.memory = memory
        self.bypass_network = bypass_network
    
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
            # compute the address
            intermediate["value"] = self.memory[self.decoded_instruction.src1]
            intermediate["type"] = "register"
            intermediate["id"] = self.decoded_instruction.dest
        elif opcode == "sw":
            intermediate["value"] = self.decoded_instruction.dest
            intermediate["type"] = "memory"
            intermediate["id"] = self.decoded_instruction.src1
        self.deallocate(intermediate)

class DispatchUnit: 
    def __init__(self, register_file, decode_buffer, alu_issue_queue, mem_issue_queue, branch_issue_queue, dispatch_width=4): 
        self.register_file = register_file
        self.decode_buffer = decode_buffer
        self.alu_issue_queue = alu_issue_queue
        self.mem_issue_queue = mem_issue_queue
        self.branch_issue_queue = branch_issue_queue
        self.busy = False
        self.dispatch_width = dispatch_width
    
    def cycle(self):
        self.busy = True
        if self.decode_buffer.is_empty():
            return
        
        for i in range(self.dispatch_width): 
            if self.decode_buffer.is_empty():
                break

            decoded_instruction = self.decode_buffer.peek()
            micro_op = decoded_instruction.micro_op
            opcode = decoded_instruction.opcode
            src1 = decoded_instruction.src1
            src2 = decoded_instruction.src2
            dest = decoded_instruction.dest

            issue_slot = IssueSlot(
                opcode = decoded_instruction.opcode,
                # micro_op = decoded_instruction.micro_op,
                dest = decoded_instruction.dest,
                src1 = decoded_instruction.src1,
                src1_ready = self.register_file.busy_table[decoded_instruction.src1] if decoded_instruction.src1 in self.register_file.busy_table.keys() else True,
                src2 = decoded_instruction.src2,
                src2_ready = self.register_file.busy_table[decoded_instruction.src2] if decoded_instruction.src2 in self.register_file.busy_table.keys() else True,
            )

            # print("Dispatching: ", issue_slot)
     
            if micro_op == "ALU":
                if self.alu_issue_queue.is_full():
                    continue
                self.alu_issue_queue.enqueue(issue_slot)
                self.decode_buffer.dequeue()
            elif micro_op == "LSU":
                if self.mem_issue_queue.is_full():
                    continue
                self.mem_issue_queue.enqueue(issue_slot)
                self.decode_buffer.dequeue()
            elif micro_op == "BRANCH":
                if self.branch_issue_queue.is_full():
                    continue
                self.branch_issue_queue.enqueue(issue_slot)
                self.decode_buffer.dequeue()

    
        self.busy = False

class IssueUnit: 
    def __init__(self, alu_issue_queue, mem_issue_queue, branch_issue_queue): 
        self.alu_issue_queue = alu_issue_queue
        self.mem_issue_queue = mem_issue_queue
        self.branch_issue_queue = branch_issue_queue
        self.busy = False
    
    def cycle(self): 
        self.busy = True
        self.alu_issue_queue.issue()
        self.mem_issue_queue.issue()
        self.branch_issue_queue.issue()
        
        self.busy = False
       
class PipelinedProcessor(CPU):
    def __init__(self, config):
        super().__init__(config) 
        self.fetch_buffer = FetchBuffer(size=config["fetch_buffer_size"])
        self.decode_buffer = DecodeBuffer(size=config["decode_buffer_size"])
        self.reorder_buffer = ReorderBuffer(reorder_buffer_size=config["reorder_buffer_size"],register_file=self.registers)
        self.bypass_network = {}
        self.alu_execution_units = [ALU(bypass_network=self.bypass_network) for i in range(config["execution_units"]["n_alus"])]
        self.mem_execution_units = [AGU(memory = self.memory, bypass_network=self.bypass_network) for i in range(config["execution_units"]["n_lsus"])]
        self.branch_execution_units = [BranchUnit(bypass_network=self.bypass_network) for i in range(config["execution_units"]["n_branch_units"])]

        self.alu_issue_queue = IssueQueue(size=config["alu_issue_queue_size"], register_file=self.registers, execution_units=self.alu_execution_units)
        self.mem_issue_queue = IssueQueue(size=config["mem_issue_queue_size"], register_file=self.registers, execution_units=self.mem_execution_units)
        self.branch_issue_queue = IssueQueue(size=config["branch_issue_queue_size"], register_file=self.registers, execution_units=self.branch_execution_units)
        self.branch_target_buffer = {}
        self.branch_history_buffer = {}
        self.branch_predictor = BranchPredictor(type=config["branch_predictor_type"])

        print(self.registers)

        self.FetchUnit = FetchUnit(
            fetch_buffer =self.fetch_buffer, 
            n_instruction_fetch_cycle = config["n_instruction_fetch_cycle"], 
            branch_predictor = self.branch_predictor,
            statistics = self.statistics
        )
        self.DecodeUnit = DecodeUnit(
            fetch_buffer = self.fetch_buffer,
            decode_buffer = self.decode_buffer,
            n_instruction_decode_cycle = config["n_instruction_decode_cycle"],
            reorder_buffer = self.reorder_buffer,
            register_file = self.registers, 
            instructions = self.config["instructions"]
        )

        self.DispatchUnit = DispatchUnit(
            register_file = self.registers,
            decode_buffer = self.decode_buffer,
            alu_issue_queue = self.alu_issue_queue,
            mem_issue_queue = self.mem_issue_queue,
            branch_issue_queue = self.branch_issue_queue,
            dispatch_width = config["dispatch_width"]
        )

        self.IssueUnit = IssueUnit(
            alu_issue_queue = self.alu_issue_queue,
            mem_issue_queue = self.mem_issue_queue,
            branch_issue_queue = self.branch_issue_queue
        )

        self.LSU = LSU(memory = self.memory, bypass_network=self.bypass_network)
        # self.ExecuteUnit = [ExecuteUnit(self.execute_buffer, config["n_instruction_execute_cycle"])]

    def fetch(self): 
        if not self.program: 
            print("no instructions to fetch as there is no program")
            return
        self.FetchUnit.cycle()

    def decode(self): 
        self.DecodeUnit.cycle()

    def dispatch(self): 
        self.DispatchUnit.cycle()

    def issue(self): 
        self.IssueUnit.cycle()

    def execute(self): 
        for unit in self.alu_execution_units: 
            unit.cycle()
        for unit in self.mem_execution_units:
            unit.cycle()
        for unit in self.branch_execution_units:
            unit.cycle()
    def memory_access(self): 
        pass
    def write_back(self): 
        pass
    def run(self, program): 
        self.program = self.assembler.assemble(program, self)
        self.FetchUnit.program = self.program
        while self.statistics["cycles"] < 100: 
            self.statistics["cycles"] += 5
            self.fetch()
            self.decode()
            self.dispatch()
            self.issue()
            self.execute()
            self.memory_access() 
            self.write_back()

            # TODO 
            # Broadcasting 
            # load store 
            # figure out how to pass data to memory and writeback stages 
            # write code for load store queue 
            # write code for the writeback stage 


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
    print(cpu.alu_issue_queue)
    # print(cpu.fetch_buffer)
    # print(cpu.decode_buffer)
    # print(cpu.reorder_buffer)
    # print(cpu.registers.RAT.free)

    # for instruction in cpu.decode_buffer: 
    #     print(instruction)