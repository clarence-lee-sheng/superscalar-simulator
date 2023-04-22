import re

def extract_reg_and_offset(operand):
    reg = re.search(r"(?<=\()(.*?)(?=\))", str(operand))
    if reg: 
        reg = reg.group(0)
        offset = int(re.search(r".*(?=\()", operand).group())
    else: 
        reg = operand
        offset = None
    
    return reg, offset

UUID = 0
def getUUID():
    global UUID
    UUID += 1
    return UUID
