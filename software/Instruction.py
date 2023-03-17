class Instruction: 
    def __init__(self, opcode, operands, cycles_to_execute):
        self.opcode = opcode
        self.operands = operands
        self.cycles_to_execute = cycles_to_execute

        if opcode in ["add", "sub", "mul", "div", "addi", "subi", "muli", "divi"]:
            self.execution_unit = "ALU"
        elif opcode in ["lw", "sw", "li", "la"]:
            self.execution_unit = "LSU"
        elif opcode in ["bne", "beq", "j", "jal", "jr"]:
            self.execution_unit = "BRANCH UNIT"

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