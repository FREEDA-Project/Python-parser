
# create a enum that can be 
# Sat(value)
# NonSat()
# Timeout()
import enum

class ResultEnum(enum.Enum):
    Sat = 1
    NonSat = 2
    Timeout = 3
    Error = 4
