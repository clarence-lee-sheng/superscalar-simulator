class BranchPredictor: 
    def __init__(self,type):
        self.type = type 
    def predict(self, branch_pc, pc): 
        if self.type == "static": 
            return branch_pc < pc
