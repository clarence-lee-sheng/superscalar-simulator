class ReservationStationInstance:
    def __init__(self, name, op, vj, vk, qj, qk, a):
        self.name = name
        self.op = op
        self.vj = vj
        self.vk = vk
        self.qj = qj
        self.qk = qk
        self.a = a
        self.busy = False
