class Memory: 
    def __init__(self, mem_size=4096):
        self.memory = [0] * mem_size
    
    def __setitem__(self, key, value): 
        self.memory[key] = value 

    def __getitem__(self, key):
        return self.memory[key] 
    
    def __str__(self): 
        return str(self.memory)

    
 