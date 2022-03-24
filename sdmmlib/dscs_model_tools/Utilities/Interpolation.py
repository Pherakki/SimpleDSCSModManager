import math


def lerp(x, y, t):
    return [(1-t)*xe + t*ye for xe, ye in zip(x, y)]


def slerp(x, y, t):
    value = min(max(sum([xe*ye for xe, ye in zip(x, y)]), -1), 1)
    omega = math.acos(value)
    
    if omega == 0 or math.isnan(omega):
        return x
    
    fac_1 = math.sin((1-t)*omega)
    fac_2 = math.sin(t*omega)
    fac_3 = math.sin(omega)
    term_1 = [xe * fac_1 for xe in x]
    term_2 = [ye * fac_2 for ye in y]
    return [(xe + ye) / fac_3 for xe, ye in zip(term_1, term_2)]
