from .BranchPredictor import BranchPredictor
from collections import defaultdict 

class TwoBitBranchPredictor(BranchPredictor): 
    def __init__(self, cpu):
        super().__init__(cpu)
        self.always_taken = True
        self.state = defaultdict(lambda: 1)
    def predict_taken(self, pc, uuid): 
        print("STATE", self.state)
        print("FETCH TARGET QUEUE", self.fetch_target_queue)
        print("BRANCH TARGET BUFFER", self.branch_target_buffer)

        if self.state[pc] >= 2: 
            return True
        else: 
            return False
    def check_prediction(self, prediction, branch_tag, uuid, pc): 
        if pc in self.branch_target_buffer.keys(): 
            taken_pc = self.branch_target_buffer[pc]
        not_taken_pc = pc + 1
        
        pred_taken = self.fetch_target_queue[uuid]
        print("PRED TAKEN", pred_taken, pc)
        print("STATE", self.state)

        pred = taken_pc if pred_taken else not_taken_pc

        print("PREDICTION", pred, prediction)

        if pred_taken and pred == prediction:
            self.state[pc] = min(3, self.state[pc] + 1)
            return True
        elif not pred_taken and pred == prediction:
            self.state[pc] = max(0, self.state[pc] - 1)
            return True
        elif pred_taken and pred != prediction:
            self.state[pc] = max(0, self.state[pc] - 1)
            return False
        elif not pred_taken and pred != prediction:
            self.state[pc] = min(3, self.state[pc] + 1)
            return False

        # if pred == prediction:
        #     self.state[pc] = min(3, self.state[pc] + 1)
        #     return True
        # else: 
        #     self.state[pc] = max(0, self.state[pc] - 1)
        #     self.branch_history_buffer = self.snapshots[branch_tag]["branch_history_buffer"]
        #     self.global_history_register = self.snapshots[branch_tag]["global_history_register"]
        #     return False
    
    
