class IssueSlot: 
    def __init__(self, pc, opcode, dest, src1, src1_ready, src2, src2_ready): 
        # this entry is based on the issue slot according to the documentation here: https://docs.boom-core.org/en/latest/sections/issue-units.html 
        self.pc = pc
        self.opcode = opcode
        self.dest = dest
        self.src1 = src1 
        self.src1_ready = src1_ready
        self.src2 = src2
        self.src2_ready = src2_ready
        # requesting is set to true when the instruction is ready to be issued, under issue slot chapter: https://docs.boom-core.org/en/latest/sections/issue-units.html
        self.requesting = src1_ready and src2_ready
    
    def __str__(self):
        return f"opcode: {self.opcode} dest: {self.dest} src1: {self.src1} src1_ready: {self.src1_ready} src2: {self.src2} src2_ready: {self.src2_ready} requesting: {self.requesting}"

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
    
    def enqueue(self, issue_entry):
        if len(self.queue) < self.size:
            self.queue.append(issue_entry)
    
    def dequeue(self):
        if len(self.queue) > 0:
            return self.queue.pop(0)
        
    def issue(self): 
        for execution_unit in self.execution_units: 
            if execution_unit.busy:
                continue 
            for i, issue_entry in enumerate(self.queue):
                print(issue_entry)
                if issue_entry.requesting:
                    print("requesting")
                    execution_unit.allocate(issue_entry)
                    self.queue.pop(i)
                break
                     
    def __str__(self):
        return str([str(i) for i in self.queue])




    
