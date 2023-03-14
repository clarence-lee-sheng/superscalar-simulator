class RegisterFile:
    def __init__(self, reg_size=32, reg_map=None): 
        self.registers = [0] * reg_size
        if not reg_map: 
            self.reg_map = {
                "zero": 0, 
                "ra": 1, 
                "sp": 2, 
                "gp": 3, 
                "tp": 4, 
                "t0": 5, 
                "t1": 6, 
                "t2": 7, 
                "s0": 8, 
                "s1": 9, 
                "a0": 10,
                "a1": 11, 
                "a2": 12, 
                "a3": 13, 
                "a4": 14, 
                "a5": 15, 
                "a6": 16, 
                "a7": 17, 
                "s2": 18, 
                "s3": 19, 
                "s4": 20, 
                "s5": 21, 
                "s6": 22, 
                "s7": 23, 
                "s8": 24, 
                "s9": 25, 
                "s10": 26, 
                "s11": 27, 
                "t3": 28, 
                "t4": 29, 
                "t5": 30, 
                "t6": 31,        
            }
        else: 
            self.reg_map = reg_map 
        assert len(self.reg_map.keys()) == reg_size, "Number of registers must correspond to the register map used"
        self.size = reg_size

    def __getitem__(self, key):
        if type(key) == str: 
            return self.registers[self.reg_map[key]]
        elif type(key) == int: 
            return self.registers[key]

    def __setitem__(self, key, value): 
        if key == "zero": 
            self.registers[self.reg_map[key]] = 0 
        else: 
            self.registers[self.reg_map[key]] = value 
            
    def __str__(self): 
        print("Values stored in registers are:")
        for name in self.reg_map.keys(): 
            print(f"{name}: {self.registers[self.reg_map[name]]}")
        return ""
    
class RegisterAllocationTable: 
    def __init__(self, num_physical_register): 
        self.num_physical_register = num_physical_register
        self.table = dict()
        self.free_list = [i for i in range(num_physical_register)]
        self.next_free = 0
        self.next_virt = 0
        
        pass 

        

