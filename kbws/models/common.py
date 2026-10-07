from enum import Enum

class NoData(str, Enum):
    twozerofour = '204'
    fourzerofour = '404'

class Quality(str, Enum):
    D = "D"
    R = "R"
    Q = "Q"
    M = "M"
    B = "B"
