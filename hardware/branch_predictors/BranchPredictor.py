from collections import deque
import copy
class BranchPredictor: 
    def __init__(self, cpu):
        n_global_history_register = cpu.config["branch_predictor"]["global_history_register_size"]
        self.cpu = cpu
        self.branch_history_buffer = {}
        self.branch_target_buffer = {}
        self.global_history_register = deque([0 for i in range(n_global_history_register)],maxlen=n_global_history_register)
        self.fetch_target_queue = {}
        self.snapshots = {}
    def predict_taken(self, branch_pc, pc): 
        pass 
    def predict(self, pc, uuid): 
        self.snapshots[uuid] = {
            "branch_history_buffer": copy.deepcopy(self.branch_history_buffer),
            "global_history_register": copy.deepcopy(self.global_history_register),
        }
        if pc in self.branch_target_buffer.keys(): 
            # print("IS IN BRANCH TARGET BUFFER", pc)
            
            taken = self.predict_taken(pc, uuid)  
            
            if taken: 
                target_pc = self.branch_target_buffer[pc]
            else: 
                target_pc =  pc + 1
            self.fetch_target_queue[uuid] = taken
        else: 
            taken = False
            target_pc = pc + 1
            self.fetch_target_queue[uuid] = False
        
        if taken: 
            self.global_history_register.appendleft(1)
        else:
            self.global_history_register.appendleft(0)
        return target_pc

    def check_prediction(self, prediction, branch_tag, uuid, pc): 
        if pc in self.branch_target_buffer.keys(): 
            taken_pc = self.branch_target_buffer[pc]
        not_taken_pc = pc + 1
        
        pred_taken = self.fetch_target_queue[uuid]

        pred = taken_pc if pred_taken else not_taken_pc
        if pred == prediction:
            return True
        else: 
            self.global_history_register.appendleft(1 if pred != pc+1 else 0)
            return False
        
