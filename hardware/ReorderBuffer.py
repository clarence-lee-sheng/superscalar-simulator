class ReorderBufferEntry: 
    def __init__(self): 
        self.reg = None
        self.value = None
        self.ready = False

class ReorderBuffer: 
    def __init__(self, reorder_buffer_size): 
        self.reorder_buffer_size = reorder_buffer_size
        self.reorder_buffer = [ReorderBufferEntry() for i in range(reorder_buffer_size)]
        self.head = 0 # points to the next available entry e.g. issue
        self.tail = 0 # points to the oldest entry e.g. commit
        self.size = 0