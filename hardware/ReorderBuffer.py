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
        return f"pc: {self.pc} type: {self.type} dest: {self.dest} value: {self.value} busy: {self.busy} valid: {self.valid} stale: {self.stale} stale_physical_destination: {self.stale_physical_destination} exception: {self.exception}"

# everytime a new instruction is met, rename and store in the reorder buffer 

class ReorderBuffer: 
    def __init__(self, cpu, reorder_buffer_size, register_file): 
        self.cpu = cpu
        self.reorder_buffer_size = reorder_buffer_size
        self.reorder_buffer = [ReorderBufferEntry() for i in range(reorder_buffer_size)]
        self.head = 0 # points to the next available entry e.g. issue
        self.tail = 1 # points to the oldest entry e.g. commit
        self.register_file = register_file

    def is_full(self): 
        if self.head % self.reorder_buffer_size == self.tail % self.reorder_buffer_size: 
            return True
        else: 
            return False
        # return self.size == self.reorder_buffer_size
    
    def enqueue(self, uuid, pc, type, dest, value, stale_physical_destination, branch_mask, ready=False): 
        if self.is_full(): 
            raise Exception
            return False
        self.reorder_buffer[self.tail].uuid = uuid
        self.reorder_buffer[self.tail].pc = pc
        self.reorder_buffer[self.tail].type = type
        self.reorder_buffer[self.tail].dest = dest
        self.reorder_buffer[self.tail].value = value
        self.reorder_buffer[self.tail].ready = ready
        self.reorder_buffer[self.tail].exception = False
        self.reorder_buffer[self.tail].stale_physical_destination = stale_physical_destination
        self.reorder_buffer[self.tail].branch_mask = branch_mask

        if self.tail == len(self.reorder_buffer) - 1: 
            self.tail = 0 
        else: 
            self.tail += 1
        return True

    def commit(self): 
        if self.head == self.tail: 
            return 
        while self.reorder_buffer[self.head].ready:
            print("COMMITTING")
            if self.reorder_buffer[self.head].value == "exit":
                self.cpu.exit = True 
            entry = self.reorder_buffer[self.head]
            if entry.stale_physical_destination is not None: 
                self.register_file.committed_map_table.free(entry.stale_physical_destination)
            # self.register_file.committed_map_table.free(entry.stale_physical_destination)
            self.reorder_buffer[self.tail] = ReorderBufferEntry()
            self.head += 1

    def flush(self, uuid):
        # flush all entries after uuid
        for i, entry in enumerate(self.reorder_buffer):
            if entry.uuid == uuid:
                break 
        self.tail = i
        # self.tail = self.head

        # rewrite stale physical destination to RAT 

    def update(self, uuid, is_exception, commit): 
        for entry in self.reorder_buffer: 
            if entry.uuid == uuid: 
                if is_exception: 
                    entry.exception = True
                if commit: 
                    entry.busy = False


    def __str__(self): 
        return str([str(rob_entry) for rob_entry in self.reorder_buffer])


