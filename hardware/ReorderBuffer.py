class ReorderBufferEntry: 
    def __init__(self): 
        self.uuid = None
        self.pc = None
        self.type = None 
        self.dest = None 
        self.value = None
        self.ready = None
        self.valid = False
        self.stale = None
        self.stale_physical_destination = None 
        self.exception = False
        self.branch_mask = None 
    
    def __str__(self): 
        return f"uuid: {self.uuid} pc: {self.pc} type: {self.type} dest: {self.dest} value: {self.value} ready: {self.ready} valid: {self.valid} stale: {self.stale} stale_physical_destination: {self.stale_physical_destination} exception: {self.exception}\n"

# everytime a new instruction is met, rename and store in the reorder buffer 

class ReorderBuffer: 
    def __init__(self, cpu, reorder_buffer_size, register_file): 
        self.cpu = cpu
        self.reorder_buffer_size = reorder_buffer_size
        self.reorder_buffer = [ReorderBufferEntry() for i in range(reorder_buffer_size)]
        self.head = 0 # points to the next available entry e.g. issue
        self.tail = 0 # points to the oldest entry e.g. commit
        self.register_file = register_file

    def is_full(self): 
        if (self.tail + 1) % self.reorder_buffer_size == self.head % self.reorder_buffer_size: 
            return True
        else: 
            return False
        # return self.size == self.reorder_buffer_size
    
    def enqueue(self, uuid, pc, type, dest, value, stale_physical_destination, branch_mask, ready=False): 
        if self.is_full(): 
            raise Exception

        self.reorder_buffer[self.tail].uuid = uuid
        self.reorder_buffer[self.tail].pc = pc
        self.reorder_buffer[self.tail].type = type
        self.reorder_buffer[self.tail].dest = dest
        self.reorder_buffer[self.tail].value = value
        self.reorder_buffer[self.tail].ready = ready
        self.reorder_buffer[self.tail].exception = False
        self.reorder_buffer[self.tail].stale_physical_destination = stale_physical_destination
        self.reorder_buffer[self.tail].branch_mask = branch_mask

        self.tail = (self.tail + 1) % self.reorder_buffer_size

        return True

    def commit(self): 
        if self.head == self.tail: 
            return 
        # print("head: ", self.head, "tail: ", self.tail)
        while self.reorder_buffer[self.head].ready:
            # if self.reorder_buffer[self.head].uuid == 726:
            #     raise Exception("726")
        
            # print("COMMITTING", self.cpu.program[self.reorder_buffer[self.head].pc])
            if self.reorder_buffer[self.head].value == "exit":
                self.cpu.exit = True 
            entry = self.reorder_buffer[self.head]
            if entry.stale_physical_destination is not None: 
                self.cpu.registers.free(entry.stale_physical_destination)
                reg = self.cpu.program[entry.pc].operands[0]
                self.cpu.registers.committed_map_table[reg] = entry.dest
            # self.register_file.committed_map_table.free(entry.stale_physical_destination)
            if self.cpu.registers.snapshots.get(entry.uuid,False):
                self.cpu.registers.snapshots.pop(entry.uuid)

            if self.cpu.program[self.reorder_buffer[self.head].pc].opcode == "sw":
                for entry in self.cpu.LSU.store_queue:
                    print("comparing uuid: ",entry.uuid, self.reorder_buffer[self.head].uuid)
                    if entry.uuid == self.reorder_buffer[self.head].uuid:
                        entry.valid = True

            self.cpu.branch_predictor.fetch_target_queue.pop(entry.uuid, None)
            self.reorder_buffer[self.tail] = ReorderBufferEntry()
            self.head += 1
            self.head = self.head % self.reorder_buffer_size
            self.cpu.statistics["instructions_count"] +=1

    def flush(self, uuid):
        # flush all entries after uuid
        tail = self.tail 
        entry = self.reorder_buffer[tail]
        flag = True
        while uuid != entry.uuid:
            if self.cpu.registers.snapshots.get(entry.uuid,False):
                # print("POPPING", entry.uuid)
                self.cpu.registers.snapshots.pop(entry.uuid)
            if entry.pc: 
                if self.cpu.program[entry.pc].opcode == "sw":
                    for s in self.cpu.LSU.store_queue:
                        self.cpu.LSU.store_queue.remove(s)

            tail = (tail - 1) % self.reorder_buffer_size
            entry = self.reorder_buffer[tail]
        if self.cpu.registers.snapshots.get(entry.uuid,False):
            self.cpu.registers.snapshots.pop(entry.uuid)
        # if self.cpu.registers.snapshots.get(entry.uuid,False):
        #     self.cpu.registers.snapshots.pop(entry.uuid)

        # if self.tail > self.head: 
        #     for i, entry in enumerate(self.reorder_buffer):
        #         if entry.uuid == 99:
        #             print("flushing: ", entry.uuid, entry.pc, entry.type, entry.dest, entry.value, entry.ready, entry.stale_physical_destination, entry.branch_mask)
        #             print(self)

        #         if entry.uuid == 116: 
        #             print("flushing 116")
                
        #         if entry.uuid == uuid:
        #             print("FLUSHING", entry.uuid)
        #             break 
        #         if self.cpu.registers.snapshots.get(entry.uuid,False):
        #             # print("POPPING", entry.uuid)
        #             self.cpu.registers.snapshots.pop(entry.uuid)
        self.tail = tail 
        # self.tail = self.head

        # rewrite stale physical destination to RAT 

    def update(self, uuid, is_exception, commit): 
        for i, entry in enumerate(self.reorder_buffer): 
            if entry.uuid == uuid: 
                if is_exception: 
                    self.reorder_buffer[i].exception = True
                if commit: 
                    self.reorder_buffer[i].ready = True


    def __str__(self): 
        output = "self.head: " + str(self.head) + " self.tail: " + str(self.tail) + "\n"
        for rob_entry in self.reorder_buffer: 
            output += str(rob_entry) + "\n"
        return output


