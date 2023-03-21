class BranchPredictor: 
    def __init__(self,type):
        self.type = type 
    def predict(self): 
        if self.type == "static": 
            return True
