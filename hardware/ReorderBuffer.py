class ReorderBufferEntry: 
    def __init__(self): 
        self.type = None 
        self.dest = None 
        self.value = None
        self.busy = True
        self.valid = False
        self.stale = None
        self.stale_physical_destination = None 
        self.exception = False

class ReorderBuffer: 
    def __init__(self, reorder_buffer_size, register_file): 
        self.reorder_buffer_size = reorder_buffer_size
        self.reorder_buffer = [ReorderBufferEntry() for i in range(reorder_buffer_size)]
        self.head = 0 # points to the next available entry e.g. issue
        self.tail = 0 # points to the oldest entry e.g. commit
        self.register_file = register_file

    def is_full(self): 
        if self.head % self.reorder_buffer_size == self.tail % self.reorder_buffer_size: 
            return True
        return self.size == self.reorder_buffer_size
    
    def enqueue(self, type, dest, value, stale_physical_destination): 
        if self.is_full(): 
            raise Exception
            return False
        self.reorder_buffer[self.tail].type = type
        self.reorder_buffer[self.tail].dest = dest
        self.reorder_buffer[self.tail].value = value
        self.reorder_buffer[self.tail].busy = True
        self.reorder_buffer[self.tail].exception = False
        self.reorder_buffer[self.tail].stale_physical_destination = stale_physical_destination

        if self.tail == len(self.reorder_buffer) - 1: 
            self.tail = 0 
        else: 
            self.tail += 1
        return True

    def commit(self): 
        if self.head == self.tail: 
            return 
        while not self.reorder_buffer[self.head].busy:
            entry = self.reorder_buffer[self.head]
            self.register_file.committed_map_table.free(entry.stale)
            self.reorder_buffer[self.tail] = ReorderBufferEntry()
            self.head += 1

    def flush(self): 
        self.tail = self.head

