from collections import deque
from copy import deepcopy


# decode reads instruction 
# assign microops and reads the source and destination registers 
# checks against the rename table and renames it to the appropriate renamed register 


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
    
class RegisterAliasTable: 
    def __init__(self, n_physical_registers, architectural_registers): 
        self.n_physical_registers = n_physical_registers

        self.table = dict()
        for i, a in enumerate(architectural_registers): 
            self.table[a] = f"P{i}"

        self.free_list = deque([f"P{i}" for i in range(n_physical_registers)])

    def __getitem__(self, key):
        print(self.table)
        return self.table[key]
    
    def __setitem__(self, key, value):
        self.table[key] = value

    def has_free(self): 
        return len(self.free_list) > 0
    
    def free(self, key): 
        assert key in ["p{i}" for i in range(self.n_physical_registers)], "Invalid physical register"
        self.free_list.appendleft(key)

    def __str__(self): 
        print("Register Alias Table:")
        print(self.table)

# ArchitectureRegisterFile 
# PhysicalRegisterFile
        
class RegisterFile: 
    def __init__(self, 
            architectural_registers = ["zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"], 
            n_physical_registers = None, 
            n_reorder_buffer_entries = 0
        ):
        if n_physical_registers is None:
            n_physical_registers = len(architectural_registers) + n_reorder_buffer_entries

        assert (n_physical_registers >= len(architectural_registers)), "Number of physical registers must be greater than or equal to the number of architectural registers"

        self.RAT = RegisterAliasTable(n_physical_registers, architectural_registers)
        self.committed_map_table = deepcopy(self.RAT)
        self.architectural_registers = architectural_registers
        self.physical_registers = [f"P{i}" for i in range(n_physical_registers)]
        self.register_file = [0] * n_physical_registers
        self.size = n_physical_registers
        self.physical_register_map = {f"P{i}": i for i in range(n_physical_registers)}

    def allocate_register(self, register_name): 
        assert self.RAT.has_free(), "No free registers available"
        if register_name == "zero": 
            return self.RAT["zero"]
        else: 
            previous_physical_register = self.RAT[register_name]
            next_free_register = self.free_list.pop()
            self.RAT[register_name] = next_free_register
            self.RAT.free(previous_physical_register)

    def rename(self, register_name, type="dest"):
        if type == "dest": 
            if self.RAT.has_free(): 
                self.allocate_register(register_name)
            else: 
                return False
        return self.RAT[register_name] 
        
    def __getitem__(self, key):
        if type(key) == str: 
            return self.register_file[self.physical_register_map[self.RAT[key]]]
        elif type(key) == int: 
            return self.register_file[key]

    def __setitem__(self, key, value): 
        if type(key) == str:
            if key == "zero": 
                self.register_file[self.RAT["zero"]] = 0 
            else: 
                self.register_file[self.physical_register_map[self.RAT[key]]] = value
        else: 
            self.physical_registers[key] = value 

    def print_rat_table(self): 
        print(self.RAT)

    def print_physical_registers(self):
        print("Values stored in physical registers are:")
        print(self.physical_registers)


