class ReservationStationInstance:
    def __init__(self, name, op, vj, vk, qj, qk, a):
        self.name = name
        self.op = op
        self.vj = vj
        self.vk = vk
        self.qj = qj
        self.qk = qk
        self.a = a
        self.busy = False


class IssueEntry: 
    def __init__(self, instruction): 
        self.op = instruction.micro_op 
        self.vj = None 
        self.vk = None 
        self.qj = 
        self.instruction = instruction 
        self.rs1 = instruction.src1
        self.rs2 = instruction.src2
        self.requesting = False
    

class IssueQueue: 
    def __init__(self, size, execution_units, register_file):
        self.size = size
        self.queue = []
        self.pc = 0
        self.execution_units = execution_units
        self.register_file = register_file

    def is_full(self):
        return len(self.queue) == self.size
    
    def is_empty(self):
        return len(self.queue) == 0
    
    def enqueue(self, instruction):
        if len(self.queue) < self.size:
            self.queue.append(instruction)
    
    def dequeue(self):
        if len(self.queue) > 0:
            return self.queue.pop(0)
        
    def issue(self): 
        for instruction in self.queue: 
            if instruction.requesting = True

        for execution_unit in self.execution_units: 
            if execution_unit.busy:
                continue 
            for i, issue_entry in enumerate(self.queue):
                if issue_entry.requesting:
                    execution_unit.allocate(issue_entry)
                     




    
