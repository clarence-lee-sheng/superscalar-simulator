class Instruction: 
    def __init__(self, pc, opcode, operands, cycles_to_execute):
        self.pc = pc
        self.micro_op = None
        self.opcode = opcode
        self.operands = operands
        self.cycles_to_execute = cycles_to_execute

    def action():
        pass 

    def __str__(self):
        return f"{self.opcode} {self.operands}"

class DecodedInstruction(Instruction): 
    def __init__(self, instruction):
        super().__init__(instruction.opcode, instruction.operands, instruction.cycles_to_execute)
        self.dest = None 
        self.src1 = None
        self.src2 = None
        self.src3 = None

    def __str__(self):
        return f"{self.instruction.opcode} {self.operands}"