from .BranchPredictor import BranchPredictor
from collections import defaultdict 

class PerceptronBranchPredictor(BranchPredictor): 
    def __init__(self, cpu):
        super().__init__(cpu)
        self.always_taken = True
        # self.weights = defaultdict(lambda: defaultdict(lambda: [0 for i in range(self.cpu.config["branch_predictor"]["global_history_register_size"])]))
        self.weights = defaultdict(lambda: defaultdict(lambda: [0 for i in range(self.cpu.config["branch_predictor"]["global_history_register_size"])]))
        self.thres = 33

    def predict_taken(self, pc, uuid): 
        weight_sum = 0 
        key = ""
        for i in self.global_history_register: 
            key += str(i)
        for i,val in enumerate(self.global_history_register): 
            if val == 0: 
                weight_sum += self.weights[key][pc][i] * -1
            else: 
                weight_sum += self.weights[key][pc][i] * 1 

        

        if pc == 15 and key == "10000": 
            print("PC 15 WEIGHT SUM: ", weight_sum, self.global_history_register, self.weights[key][pc])
        if pc == 15: 
            print("KEY for pc 15 is: ", key, "WEIGHT sum is: ", weight_sum)
        if weight_sum > 0: 
            return True 
        else: 
            return False 
            

    def update(self, pc, key, pred): 
        weights = self.weights[key]

        if pc == 15: 
            print("UPDATING KEY: ", key)
        
        print("Before: ", weights,"Key: ", key)
        for i,val in enumerate(key): 
            if val == "0": 
                if pred: 
                    weights[pc][i] -= 1
                else: 
                    weights[pc][i] += 1
            elif val == "1": 
                if pred: 
                    weights[pc][i] += 1
                else: 
                    weights[pc][i] -= 1
            weights[pc][i] = max(-14, min(14, weights[pc][i]))
        print("After: ", weights)
        self.weights[key] = weights


    def check_prediction(self, gt, branch_tag, uuid, pc): 
        # print(self.snapshots)
        global_history_register = self.snapshots[uuid]["global_history_register"]
        key = ""
        print("global history register: ", global_history_register)
        for i in global_history_register:
            key += str(i)
        if pc in self.branch_target_buffer.keys(): 
            taken_pc = self.branch_target_buffer[pc]
        not_taken_pc = pc + 1
        
        pred_taken = self.fetch_target_queue[uuid]

        pred = taken_pc if pred_taken else not_taken_pc
        target = pred_taken if pred == gt else not pred_taken
        self.update(pc, key, target)

        if pred == gt:
            if pc == 15 and key == "10000000000000000010": 
                print("gt CORRECT", pred, gt, "PC: ", pc, uuid, global_history_register)
                print(self.cpu.program[pc])
            return True
        else: 
            print("gt FAILED", pred, gt, "PC: ", pc, uuid, global_history_register, key, str(self.snapshots[uuid]["global_history_register"]))
            print(self.cpu.program[pc])
            self.branch_history_buffer = self.snapshots[uuid]["branch_history_buffer"]
            self.global_history_register = self.snapshots[uuid]["global_history_register"]
            self.global_history_register.appendleft(1 if pred != pc+1 else 0)
            
            return False