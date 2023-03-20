class Buffer: 
    def __init__(self, size):
        self.size = size
        self.queue = []

    def is_full(self):
        return len(self.queue) == self.size
    
    def enqueue(self, instruction):
        if len(self.queue) < self.size:
            self.queue.append(instruction)

    def dequeue(self):
        if len(self.queue) > 0:
            return self.queue.pop(0)
        
    def __str__(self):
        return str(self.queue)
    
    def __iter__(self):
        for ins in self.queue:
            yield ins

class FetchBuffer(Buffer):
    def __init__(self, size):
        super().__init__(size)
        self.pc = 0

class DecodeBuffer(Buffer):
    def __init__(self, size):
        super().__init__(size)
        self.pc = 0

    