from hardware.RegisterFile import RegisterFile
from hardware.Memory import Memory 
from hardware.CPU import CPU
from hardware.Buffer import FetchBuffer, DecodeBuffer
from hardware.ReorderBuffer import ReorderBuffer, ReorderBufferEntry
from hardware.branch_predictors.StaticBranchPredictor import StaticBranchPredictor
from hardware.branch_predictors.TwoBitBranchPredictor import TwoBitBranchPredictor
from hardware.branch_predictors.OneBitBranchPredictor import OneBitBranchPredictor
from hardware.branch_predictors.PerceptronBranchPredictor import PerceptronBranchPredictor
# from hardware.BranchPredictor import BranchPredictor
from hardware.IssueQueue import IssueQueue, IssueSlot
from software.Assembler import Assembler 
from software.Instruction import DecodedInstruction
from utils.utils import extract_reg_and_offset, getUUID
import json

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
config = json.load(open("./config.json"))


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
    def __init__(self,cpu, fetch_buffer, n_instruction_fetch_cycle,branch_predictor, statistics={}, program=None): 
        self.cpu = cpu
        self.program = program
        self.fetch_buffer = fetch_buffer
        self.n_instruction_fetch_cycle = n_instruction_fetch_cycle
        self.statistics = statistics
        self.branch_predictor = branch_predictor
        self.busy = True
    
    def cycle(self): 
        self.busy = True
        if self.fetch_buffer.is_full():
            return
        
        for i in range(self.n_instruction_fetch_cycle):
            uuid = getUUID()
            
            
            
            if self.fetch_buffer.is_full():
                # print("fetch buffer is full")
                break
            if self.cpu.pc >= len(self.program): 
                # print("no more instructions to fetch", self.cpu.pc)
                break

            instruction = self.program[self.cpu.pc]
            # print("fetching instruction", self.cpu.pc, instruction)
            
            
            instruction.uuid = uuid
            self.fetch_buffer.enqueue(instruction)

            # self.statistics["instructions_count"] += 1
            # opcode = instruction.opcode
            # if opcode == "lw" or opcode == "li" or opcode == "la":
            #     self.statistics["load_count"] += 1
            # if opcode == "sw":
            #     self.statistics["store_count"] += 1
            # if opcode == "beq" or opcode == "bne" or opcode == "bge" or opcode == "bgt" or opcode == "ble" or opcode == "blt":
            #     self.statistics["branch_count"] += 1

            next_pc = self.branch_predictor.predict(instruction.pc, instruction.uuid)
            self.cpu.pc = next_pc
            
        self.busy = False
        
class DecodeUnit: 
    def __init__(self, cpu, fetch_buffer, decode_buffer, n_instruction_decode_cycle, reorder_buffer, register_file, instructions): 
        self.cpu = cpu
        self.fetch_buffer = fetch_buffer
        self.decode_buffer = decode_buffer
        self.reorder_buffer = reorder_buffer
        self.n_instruction_decode_cycle = n_instruction_decode_cycle
        self.register_file = register_file
        self.busy = False 
        self.instructions = instructions
        self.branch_mask = 0

    def cycle(self): 
        # print("----------------------------------------------------------------")
        # print("DECODE STAGE")
        self.busy = True
        if self.decode_buffer.is_full():
            return
        
        def rename(instruction): 
            stale_physical_register = None 
            if instruction.src1: 
                instruction.src1 = self.register_file.rename(instruction.src1, type="src")
            if instruction.src2: 
                instruction.src2 = self.register_file.rename(instruction.src2, type="src")
            if instruction.src3:
                instruction.src3 = self.register_file.rename(instruction.src3, type="src")
            if instruction.dest:
                instruction.dest, stale_physical_register = self.register_file.rename(instruction.dest, type ="dest")
            return instruction, stale_physical_register
        
        for i in range(self.n_instruction_decode_cycle): 
            if self.decode_buffer.is_full() or self.reorder_buffer.is_full() or not self.register_file.RAT.has_free(): 
                # print("reorder buffer is full", self.reorder_buffer.is_full(), self.reorder_buffer.tail, self.reorder_buffer.head)
                # print(self.reorder_buffer.reorder_buffer[self.reorder_buffer.head], self.reorder_buffer.reorder_buffer[self.reorder_buffer.tail])
                # print("RAT is full", not self.register_file.RAT.has_free())
                break
            if self.fetch_buffer.is_empty():
                break
            instruction = self.fetch_buffer.dequeue()
            opcode = instruction.opcode
            operands = instruction.operands
            if opcode == "ecall" or opcode == "exit": 
                dest = None
                src1 = None
                src2 = None
                src3 = None
                decoded_instruction = DecodedInstruction(instruction=instruction, dest=dest, src1=src1, src2=src2, src3=src3)
            elif opcode not in self.instructions["branch_instructions"] and opcode not in self.instructions["jump_instructions"] and opcode not in ["sw"]: 
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

            # print("DECODE*** original instruction", decoded_instruction, end = " ")
            decoded_instruction, stale_physical_register = rename(decoded_instruction)
            # print("renamed instruction", decoded_instruction.dest)
            if opcode in self.instructions["alu_instructions"]:
                decoded_instruction.micro_op = "ALU"
            elif opcode in self.instructions["load_store_instructions"]:
                decoded_instruction.micro_op = "LSU"
            elif opcode in self.instructions["branch_instructions"] or opcode in self.instructions["jump_instructions"]:
                # decoded_instruction.micro_op = "BRANCH UNIT"
                decoded_instruction.micro_op = "BRANCH"
                self.branch_mask += 1
                self.cpu.registers.snapshot(decoded_instruction.uuid, decoded_instruction)
            type = decoded_instruction.micro_op
            pc = decoded_instruction.pc
            dest = decoded_instruction.dest
            uuid = decoded_instruction.uuid
            value = None 

            if decoded_instruction.opcode == "exit": 
                value = "exit"

            # self.cpu.branch_predictor.snapshot(pc, self.branch_mask)
            decoded_instruction.branch_mask = self.branch_mask

            self.decode_buffer.enqueue(decoded_instruction)
            if opcode in ["ecall", "exit"]: 
                self.reorder_buffer.enqueue(uuid, pc, type, dest, value, stale_physical_register, self.branch_mask, ready=True)
            else: 
                self.reorder_buffer.enqueue(uuid, pc, type, dest, value, stale_physical_register, self.branch_mask)

        self.busy = False 
        # print("----------------------------------------------------------------")

class BranchUnit: 
    def __init__(self, cpu): 
        self.branch_instruction = None 
        self.cycles_executed = 0
        self.busy = False
        self.bypass_network = cpu.bypass_network
        self.branch_predictor = cpu.branch_predictor
        self.registers = cpu.registers
        self.cpu = cpu
    def allocate(self, branch_instruction): 
        self.busy = True
        self.branch_instruction = branch_instruction
    def deallocate(self): 
        self.busy = False
        self.cycles_executed = 0
        self.branch_instruction = None
    def cycle(self): 
        # print("Branch Unit: ", self.branch_instruction)
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.branch_instruction.instruction.cycles_to_execute:
            return 
        opcode = self.branch_instruction.opcode

        if opcode == "j": 
            target = self.branch_instruction.src1
            taken = True
        elif opcode == "beq":
            result = self.cpu.get_register_or_forwarded(self.branch_instruction.src1) == self.cpu.get_register_or_forwarded(self.branch_instruction.src2)
            # print("BEQ, ", self.branch_instruction.instruction.branch_mask, "pc: ",self.branch_instruction.pc,  self.cpu.get_register_or_forwarded(self.branch_instruction.src1), self.cpu.get_register_or_forwarded(self.branch_instruction.src2), "result: ", result)
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) == self.cpu.get_register_or_forwarded(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "bne":
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) != self.cpu.get_register_or_forwarded(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
            # print("IS TAKEN: ", taken)
        elif opcode == "bge": 
            # print("bge", self.cpu.get_register_or_forwarded(self.branch_instruction.src1), self.cpu.get_register_or_forwarded(self.branch_instruction.src2))
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) >= self.cpu.get_register_or_forwarded(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else: 
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "blt":
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) < self.cpu.get_register_or_forwarded(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "bgeu":
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) >= float(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "bltu":
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) < float(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "bleu": 
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) <= float(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False
        elif opcode == "bgtu":
            if self.cpu.get_register_or_forwarded(self.branch_instruction.src1) > float(self.branch_instruction.src2):
                target = self.branch_instruction.instruction.src3
                taken = True
            else:
                target = self.branch_instruction.pc + 1
                taken = False

        if taken: 
            cpu.branch_predictor.branch_target_buffer[self.branch_instruction.pc] = target  

        is_correct = cpu.branch_predictor.check_prediction(target, self.branch_instruction.instruction.branch_mask, self.branch_instruction.uuid, self.branch_instruction.pc) 
        self.cpu.statistics["branch_count"] += 1
        self.cpu.statistics["branches_executed"][opcode] += 1

        if is_correct: 
            self.cpu.statistics["correct_branch_count"] += 1
        else: 
            self.cpu.statistics["mispredicted_branch_count"] += 1

        # print("IS CORRECT", is_correct)
        
        if not is_correct:
            
            self.cpu.pc = target
            self.cpu.reorder_buffer.update(self.branch_instruction.uuid, is_exception=True, commit=True)
            
            # print("FLUSHING", self.branch_instruction)
            self.cpu.branch_mispredict_flush(self.branch_instruction.instruction.branch_mask, self.branch_instruction.uuid)
            # if self.branch_instruction.uuid == 33: 
            #     print("MISPREDICTED BRANCH", self.branch_instruction)
            #     print(self.cpu.reorder_buffer)
        else: 
            self.cpu.reorder_buffer.update(self.branch_instruction.uuid, is_exception=False, commit=True)
        self.busy = False
        self.deallocate()

class BaseUnit: 
    def __init__(self, cpu): 
        self.cpu = cpu 

    def broadcast(self, reg, result): 
        # print("broadcasting ", reg, result)
        self.cpu.bypass_network[reg] = result
        for queue in self.cpu.issue_queues:
            for issue_slot in queue.queue: 
                src1_reg, offset = extract_reg_and_offset(issue_slot.src1)
                src2_reg, offset = extract_reg_and_offset(issue_slot.src2)

                if src1_reg == reg:
                    issue_slot.src1_ready = True
                if src2_reg == reg:
                    issue_slot.src2_ready = True
                if issue_slot.src1_ready and issue_slot.src2_ready: 
                    issue_slot.requesting = True

class ALU(BaseUnit):
    def __init__(self, cpu, bypass_network, issue_queues): 
        super().__init__(cpu)
        self.cpu = cpu
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
        self.decoded_instruction = None
        return result
    def cycle(self): 
        # print("ALU: ", self.decoded_instruction)
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.decoded_instruction.instruction.cycles_to_execute:
            return 
        intermediate = dict()
        opcode = self.decoded_instruction.opcode

        if opcode == "add":
            # print("ADD, ","pc: ", self.decoded_instruction.pc, self.decoded_instruction.src1, self.cpu.get_register_or_forwarded(self.decoded_instruction.src1), self.decoded_instruction.src2, self.cpu.get_register_or_forwarded(self.decoded_instruction.src2))
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) + int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src2))
            reg = self.decoded_instruction.dest
        elif opcode == "sub":
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) - int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src2))
            reg = self.decoded_instruction.dest
        elif opcode == "subi":
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) - int(self.decoded_instruction.src2)
            reg = self.decoded_instruction.dest
        elif opcode == "div": 
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) // int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src2))
            reg = self.decoded_instruction.dest
        elif opcode == "mul": 
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) * int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src2))
            reg = self.decoded_instruction.dest
        elif opcode == "addi":  
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) + int(self.decoded_instruction.src2)
            reg = self.decoded_instruction.dest
        elif opcode == "remw": 
            result = int(self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)) % int(self.decoded_instruction.src2)
            reg = self.decoded_instruction.dest
        elif opcode == "ecall":
            intermediate["value"] = None 
            intermediate["type"] = "sys"
            intermediate["id"] = None 
        self.broadcast(reg, result)
        self.cpu.reorder_buffer.update(self.decoded_instruction.uuid, is_exception=False, commit=True)
        if opcode in ["sub", "subi", "div", "add", "addi", "mul", "remw"]:
            # print("ADDING to write back queue")
            self.cpu.write_back_queue.append({"uuid": self.decoded_instruction.uuid, "dest": reg, "value": result})

        self.deallocate(intermediate)


# Address generation unit 
# 1. instruction come in 
# 2. read the operands and compute the address 

class AGU(BaseUnit): 
    def __init__(self, cpu, register_file, memory, bypass_network, issue_queues, LSU): 
        super().__init__(cpu)
        self.cpu = cpu
        self.busy = False
        self.cycle_time = 3
        self.cycles_executed = 0
        self.decoded_instruction = None
        self.register_file = register_file
        self.memory = memory
        self.bypass_network = bypass_network
        self.LSU = LSU

    def allocate(self, decoded_instruction):
        self.busy = True
        self.decoded_instruction = decoded_instruction
    def deallocate(self):
        # print("DEALLOCATE AGU")
        self.busy = False
        self.decoded_instruction = None
        self.cycles_executed = 0

    def cycle(self):
        # print("AGU: ", self.decoded_instruction)
        if not self.busy:
            return 
        self.cycles_executed += 1
        if self.cycles_executed < self.decoded_instruction.instruction.cycles_to_execute:
            return 
        opcode = self.decoded_instruction.opcode
        reg, result = None, None
        if opcode == "li": 
            valid = True 
            data = self.decoded_instruction.src1
            dest =  self.decoded_instruction.dest
            addr = None 
            entry_type = "load"
            reg = dest
            result = data

            self.cpu.write_back_queue.append({"uuid": self.decoded_instruction.uuid, "dest": reg, "value": result })
            # self.cpu.reorder_buffer.update(self.decoded_instruction.uuid, is_exception=False, commit=True)

        elif opcode == "la":
            valid = True
            data = None
            dest = self.decoded_instruction.dest
            addr = self.decoded_instruction.src1

            reg = dest
            result = addr

            self.cpu.write_back_queue.append({"uuid": self.decoded_instruction.uuid, "dest": reg, "value": result })
            # self.cpu.reorder_buffer.update(self.decoded_instruction.uuid, is_exception=False, commit=True)
            
        elif opcode == "lw":
            reg, offset = extract_reg_and_offset(self.decoded_instruction.src1)
            if self.register_file.busy_table[reg]: 
                addr = offset + self.register_file[reg]
            else: 
                addr = offset + self.bypass_network[reg]
            dest = self.decoded_instruction.dest
            result = None 
            valid = True
            data = None
            entry_type = "load"

            lsu_entry = LSU_entry(self.decoded_instruction.pc, self.decoded_instruction.uuid, valid, addr, data, entry_type, dest)
            self.LSU.enqueue(lsu_entry)
            # compute the address

        elif opcode == "sw":
            reg, offset = extract_reg_and_offset(self.decoded_instruction.src2)
            if self.register_file.busy_table[reg]: 
                addr = offset + self.register_file[reg]
            else: 
                addr = offset + self.bypass_network[reg]
            entry_type = "store"

            dest = None
            result = None 
            valid = False
            data = self.cpu.get_register_or_forwarded(self.decoded_instruction.src1)
            # print("DATA", self.decoded_instruction.src1, data)

            lsu_entry = LSU_entry(self.decoded_instruction.pc, self.decoded_instruction.uuid, valid, addr, data, entry_type, dest)
            self.LSU.enqueue(lsu_entry)
        else: 
            raise Exception("Invalid opcode for AGU", opcode)
        self.cpu.reorder_buffer.update(self.decoded_instruction.uuid, is_exception=False, commit=True)
        
        if reg is not None and result is not None: 
            self.broadcast(reg, result)
        
        self.deallocate()


class LSU_entry: 
    def __init__(self, pc, uuid, valid, addr, data, type, dest=None): 
        self.valid = valid
        self.addr = addr
        self.data = data
        self.pc = pc
        self.uuid = uuid
        self.type = type
        self.dest = dest
    def __str__(self) -> str:
        return f"pc: {self.pc}, valid: {self.valid}, addr: {self.addr}, data: {self.data}, dest: {self.dest}, type: {self.type}"
        pass
    

class LSU(BaseUnit): 
    def __init__(self, cpu, memory, bypass_network):
        super().__init__(cpu)
        self.cpu = cpu 
        self.busy = False
        self.load_cycle_time = 2
        self.store_cycle_time = 2
        self.cycles_executed = 0
        self.decoded_instruction = None
        self.memory = memory
        self.bypass_network = bypass_network
        # self.queue = list()
        self.load_queue = list()
        self.store_queue = list()
        self.n_memory_ports_load = 2
        self.n_memory_ports_store = 2

    def enqueue(self, lsu_entry):
        if lsu_entry.type == "load":
            self.load_queue.append(lsu_entry)
        elif lsu_entry.type == "store":
            self.store_queue.append(lsu_entry)
        # self.lsu_queue.append(lsu_entry)
    
    def allocate(self, decoded_instruction):
        self.busy = True
        self.decoded_instruction = decoded_instruction
    
    def deallocate(self):
        self.busy = False
        self.decoded_instruction = None
        self.cycles_executed = 0
        return 
    
    def cycle(self): 
        # print("load queue: ", [str(i) for i in self.load_queue])
        # print("store queue: ", [str(i) for i in self.store_queue])
        for i in range(self.n_memory_ports_load):
            for entry in self.load_queue: 
                if entry.valid: 
                    # print("memory access: ", entry)
                    entry.data = self.memory[entry.addr]
                    self.broadcast(entry.dest, entry.data)
                    self.cpu.write_back_queue.append({"uuid": entry.uuid, "dest": entry.dest, "value": entry.data })
                    self.cpu.reorder_buffer.update(entry.uuid, is_exception=False, commit=True)
                    self.load_queue.remove(entry)
                    
        for i in range(self.n_memory_ports_store):
            for entry in self.store_queue: 
                if entry.valid: 
                    # print("Storing: ", entry.data, "at", entry.addr)
                    self.memory[entry.addr] = entry.data
                    self.store_queue.remove(entry)
                    
 
        
class DispatchUnit: 
    def __init__(self, cpu, register_file, decode_buffer, alu_issue_queue, mem_issue_queue, branch_issue_queue, dispatch_width=4): 
        self.cpu = cpu
        self.register_file = register_file
        self.decode_buffer = decode_buffer
        self.alu_issue_queue = alu_issue_queue
        self.mem_issue_queue = mem_issue_queue
        self.branch_issue_queue = branch_issue_queue
        self.busy = False
        self.dispatch_width = dispatch_width
    
    def cycle(self):
        # print("----------------------------------------------------------------")
        # print("DISPATCH")
        self.busy = True
        if self.decode_buffer.is_empty():
            return
        
        for i in range(self.dispatch_width): 
            if self.decode_buffer.is_empty():
                break

            decoded_instruction = self.decode_buffer.peek()
            uuid = decoded_instruction.uuid
            micro_op = decoded_instruction.micro_op
            pc = decoded_instruction.pc
            opcode = decoded_instruction.opcode
            dest = decoded_instruction.dest
            src1 = decoded_instruction.src1
            src2 = decoded_instruction.src2

            reg, offset = extract_reg_and_offset(src1)
            if reg in self.register_file.busy_table.keys():
                src1_ready = self.register_file.busy_table[reg]
                if reg in self.cpu.bypass_network.keys():
                    src1_ready = True
            else:
                src1_ready = True
            
            reg, offset = extract_reg_and_offset(src2)
            if reg in self.register_file.busy_table.keys():
                src2_ready = self.register_file.busy_table[reg]
                if reg in self.cpu.bypass_network.keys():
                    src2_ready = True
            else:
                src2_ready = True

            issue_slot = IssueSlot(
                uuid = uuid,
                pc = pc,
                opcode = opcode,
                # micro_op = decoded_instruction.micro_op,
                dest = dest,
                src1 = src1,
                src1_ready = src1_ready,
                src2 = src2,
                src2_ready = src2_ready,
                instruction = decoded_instruction
            )
     
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
        # print("----------------------------------------------------------------")

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
        self.reorder_buffer = ReorderBuffer(cpu=self,reorder_buffer_size=config["reorder_buffer_size"],register_file=self.registers)
        self.write_back_queue = []
        self.bypass_network = {}
        # self.branch_predictor = StaticBranchPredictor(cpu = self)
        # self.branch_predictor = TwoBitBranchPredictor(cpu = self)

        if config["branch_predictor"]["type"] == "static_taken":
            self.branch_predictor = StaticBranchPredictor(cpu = self, always_taken=True)
        elif config["branch_predictor"]["type"] == "static_not_taken":
            self.branch_predictor = StaticBranchPredictor(cpu = self, always_taken=False)
        elif config["branch_predictor"]["type"] == "one_bit":
            self.branch_predictor = OneBitBranchPredictor(cpu = self)
        elif config["branch_predictor"]["type"] == "two_bit":
            self.branch_predictor = TwoBitBranchPredictor(cpu = self)
        elif config["branch_predictor"]["type"] == "perceptron":
            self.branch_predictor = PerceptronBranchPredictor(cpu = self)

        self.alu_issue_queue = IssueQueue(size=config["alu_issue_queue_size"], register_file=self.registers)
        self.mem_issue_queue = IssueQueue(size=config["mem_issue_queue_size"], register_file=self.registers)
        self.branch_issue_queue = IssueQueue(size=config["branch_issue_queue_size"], register_file=self.registers)

        issue_queues = [self.alu_issue_queue, self.mem_issue_queue, self.branch_issue_queue]
        self.issue_queues = issue_queues

        self.LSU = LSU(
            cpu = self,
            memory = self.memory,
            bypass_network = self.bypass_network
        )

        self.alu_execution_units = [ALU(cpu=self, bypass_network=self.bypass_network, issue_queues=self.issue_queues) for i in range(config["execution_units"]["n_alus"])]
        self.mem_execution_units = [AGU(cpu=self, register_file = self.registers, memory = self.memory, bypass_network=self.bypass_network,issue_queues=self.issue_queues,  LSU=self.LSU) for i in range(config["execution_units"]["n_lsus"])]
        self.branch_execution_units = [BranchUnit(cpu=self) for i in range(config["execution_units"]["n_branch_units"])]

        self.alu_issue_queue.execution_units = self.alu_execution_units
        self.mem_issue_queue.execution_units = self.mem_execution_units
        self.branch_issue_queue.execution_units = self.branch_execution_units

        self.FetchUnit = FetchUnit(
            cpu = self,
            fetch_buffer =self.fetch_buffer, 
            n_instruction_fetch_cycle = config["n_instruction_fetch_cycle"], 
            branch_predictor = self.branch_predictor,
            statistics = self.statistics
        )
        self.DecodeUnit = DecodeUnit(
            cpu = self,
            fetch_buffer = self.fetch_buffer,
            decode_buffer = self.decode_buffer,
            n_instruction_decode_cycle = config["n_instruction_decode_cycle"],
            reorder_buffer = self.reorder_buffer,
            register_file = self.registers, 
            instructions = self.config["instructions"]
        )

        self.DispatchUnit = DispatchUnit(
            cpu = self,
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
        # self.ExecuteUnit = [ExecuteUnit(self.execute_buffer, config["n_instruction_execute_cycle"])]

    def fetch(self): 
        if not self.program: 
            # print("no instructions to fetch as there is no program")
            return
        self.FetchUnit.cycle()

    def decode(self): 
        self.DecodeUnit.cycle()

    def dispatch(self): 
        self.DispatchUnit.cycle()

    def issue(self): 
        self.IssueUnit.cycle()

    def execute(self): 
        # print("alu issue queue: ",  self.alu_issue_queue)
        # print("mem issue queue: ",  self.mem_issue_queue)
        # print("branch issue queue: ", self.branch_issue_queue)
        # print("alu issue queue length: ", len(self.alu_issue_queue.queue))
        # print("mem issue queue length: ", len(self.mem_issue_queue.queue))
        # print("branch issue queue length: ", len(self.branch_issue_queue.queue))
        for unit in self.alu_execution_units: 
            unit.cycle()
        for unit in self.mem_execution_units:
            unit.cycle()
        for unit in self.branch_execution_units:
            unit.cycle()
    def memory_access(self): 
        self.LSU.cycle()
    def write_back(self): 
        # print("WRITE BACK QUEUE: ", self.write_back_queue)
        for entry in self.write_back_queue:
            # print("Writing back: dest: ", entry["dest"], "value: ", entry["value"])
            self.registers[entry["dest"]] = entry["value"]
            self.registers.busy_table[entry["dest"]] = True
            # print("***Busy table: ", self.registers.busy_table)

            if entry["dest"] in self.bypass_network: 
                self.bypass_network.pop(entry["dest"])

        # print("busy table: ", self.registers.busy_table)
        self.write_back_queue = []


    def branch_mispredict_flush(self, branch_mask=None, uuid=None): 
        # print("flushing")
        cpu.fetch_buffer.flush()
        cpu.decode_buffer.flush()
        cpu.alu_issue_queue.flush(branch_mask = branch_mask)
        cpu.mem_issue_queue.flush(branch_mask = branch_mask)
        cpu.branch_issue_queue.flush(branch_mask = branch_mask)
        # print("reorder buffer flushed", branch_mask)
        cpu.registers.restore(uuid = uuid)
        # print("flushing reorder buffer")
        cpu.reorder_buffer.flush(uuid = uuid)
        
        # print("flushing done")

    def get_register_or_forwarded(self, reg): 
        # print("Register: ", reg)
        # print("Bypass network: ", self.bypass_network)
        # print(self.registers.busy_table)
        if self.registers.busy_table[reg]: 
            return self.registers[reg]
        elif reg in self.bypass_network.keys():
            return self.bypass_network[reg]
        else: 
            raise Exception("Register not found")
    def run(self, program): 
        self.exit = False
        self.program = self.assembler.assemble(program, self)
        self.FetchUnit.program = self.program
        while self.statistics["cycles"] <1000000: 
            self.statistics["cycles"] += 1
            print("Cycle: ", self.statistics["cycles"])
            self.reorder_buffer.commit() 
            self.write_back() 
            self.memory_access() 
            self.execute() 
            self.issue() 
            self.dispatch()
            self.decode() 
            self.fetch() 

            if self.exit: 
                break

            # print(self.reorder_buffer)
            # print("BUSY_TABLE",self.registers.busy_table["P97"])
            # print("FREE LIST:", self.registers.RAT.free_list)
            # print("Reorder buffer: ", self.reorder_buffer)
            # print("Reorder buffer tail and head: ", self.reorder_buffer.tail, self.reorder_buffer.head)
            # print("Reorder buffer head: ", self.reorder_buffer.reorder_buffer[self.reorder_buffer.head])
            # print("fetch buffer length: ", len(self.fetch_buffer.queue))
            # print("decode buffer length: ", len(self.decode_buffer.queue))
            # print("write back queue length: ", len(self.write_back_queue))
            # print("Bypass network: ", self.bypass_network)
            # print(self.registers.register_file)
            # print("Memory: ", self.memory[:40])
            print("-----------------------------------------")

        print("Number of instructions executed: ", self.statistics["instructions_count"])
        print("Number of cycles: ", self.statistics["cycles"])
        print("Instruction per cycle: ", self.statistics["instructions_count"]/self.statistics["cycles"])
        print("Cycles per instruction: ", self.statistics["cycles"]/self.statistics["instructions_count"])
        print("Number of stores executed: ", self.statistics["store_count"])
        print("Number of loads executed: ", self.statistics["load_count"])
        print("Number of branches executed: ", self.statistics["branch_count"])
        print("Number of mispredicted branches: ", self.statistics["mispredicted_branch_count"])
        print("Number of correct branches: ", self.statistics["correct_branch_count"])
        print("Branch prediction accuracy: ", 1 - self.statistics["mispredicted_branch_count"]/self.statistics["branch_count"])
        print("Branch accuracy: ", self.statistics["correct_branch_count"]/(self.statistics["mispredicted_branch_count"] + self.statistics["correct_branch_count"]))
        print("Branches executed: ", self.statistics["branches_executed"])
        
    
if __name__ == "__main__": 
    cpu = PipelinedProcessor(config)
    # cpu.run(os.path.join(os.getcwd(), "programs\\vec_addition.s"))
    # cpu.run(os.path.join(os.getcwd(), "programs\\matrix_multiplication.s"))
    # cpu.run(os.path.join(os.getcwd(), "programs\\odd_counts.s"))
    cpu.run(os.path.join(os.getcwd(), "programs\\decisiontreeclassifier.s"))
    # cpu.run(os.path.join(os.getcwd(), "programs\\convolution.s"))

    # print(cpu.alu_issue_queue)
    # print(cpu.LSU.load_queue)
    # for entry in cpu.LSU.load_queue: 
    #     print(entry)
    # print(cpu.memory[:40])
    # print(cpu.reorder_buffer)
    print(cpu.fetch_buffer)
    print(cpu.bypass_network)
    print(cpu.branch_predictor.branch_target_buffer)
    print(cpu.memory[90:120])
    print(cpu.registers.snapshots.keys())
    # print(cpu.registers.register_file)
    # print(cpu.registers.busy_table)
    # print(cpu.reorder_buffer)
    # print(cpu.registers.RAT.free)

    # for instruction in cpu.decode_buffer: 
    #     print(instruction)