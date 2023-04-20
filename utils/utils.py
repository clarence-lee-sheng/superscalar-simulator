import re

def extract_reg_and_offset(operand):
    reg = re.search(r"(?<=\()(.*?)(?=\))", str(operand))
    if reg: 
        reg = reg.group(0)
        offset = re.search(r".*(?=\()", operand).group()
    else: 
        reg = operand
        offset = None
    
    return reg, offset
