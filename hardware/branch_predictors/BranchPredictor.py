class BranchPredictor: 
    def __init__(self, cpu):
        self.cpu = cpu
        self.branch_history_buffer = {}
        self.branch_target_buffer = {}
        self.global_history_register = {}
        self.fetch_target_queue = {}
        self.snapshots = {}
    def predict_taken(self, branch_pc, pc): 
        pass 
    def predict(self, pc, uuid): 
        if pc in self.branch_target_buffer.keys(): 
            print("IS IN BRANCH TARGET BUFFER", pc)
            taken = self.predict_taken(pc, uuid)  
            if taken: 
                target_pc = self.branch_target_buffer[pc]
            else: 
                target_pc =  pc + 1
            self.fetch_target_queue[uuid] = taken
        else: 
            target_pc = pc + 1
            self.fetch_target_queue[uuid] = False
        
        return target_pc
    def snapshot(self, pc, branch_tag): 
        self.snapshots[branch_tag] = {
            "branch_history_buffer": self.branch_history_buffer,
            "global_history_register": self.global_history_register,
        }
    
    def check_prediction(self, prediction, branch_tag, uuid, pc): 
        if uuid in self.fetch_target_queue.keys(): 
            pred = self.fetch_target_queue[uuid]
        else: 
            pred = pc + 1


        if pred == prediction:
            return True
        else: 
            self.branch_history_buffer = self.snapshots[branch_tag]["branch_history_buffer"]
            self.global_history_register = self.snapshots[branch_tag]["global_history_register"]
            return False
        
