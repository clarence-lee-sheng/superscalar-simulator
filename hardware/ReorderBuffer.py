class ReorderBufferEntry: 
    def __init__(self): 
        self.type = None 
        self.dest = None 
        self.value = None
        self.ready = False

class ReorderBuffer: 
    def __init__(self, reorder_buffer_size): 
        self.reorder_buffer_size = reorder_buffer_size
        self.reorder_buffer = [ReorderBufferEntry() for i in range(reorder_buffer_size)]
        self.head = 0 # points to the next available entry e.g. issue
        self.tail = 0 # points to the oldest entry e.g. commit

    def is_full(self): 
        if self.head % self.reorder_buffer_size == self.tail % self.reorder_buffer_size: 
            return True
        return self.size == self.reorder_buffer_size
    
    def enqueue(self, type, dest, value): 
        if self.is_full(): 
            print("buffer full, stalling")
            return False
        self.reorder_buffer[self.head].type = type
        self.reorder_buffer[self.head].dest = dest
        self.reorder_buffer[self.head].value = value
        self.reorder_buffer[self.head].ready = False
        self.tail += 1
        return True

    def commit(self): 
        if self.head == self.tail: 
            raise Exception("Nothing to commit")
        if self.reorder_buffer[self.tail].ready:
            self.reorder_buffer[self.tail] = ReorderBufferEntry()
            self.head += 1

