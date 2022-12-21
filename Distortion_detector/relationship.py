import math

def relationship(c1, c2):
    [x1, y1, x2, y2] = c1
    [x3, y3, x4, y4] = c2
    out = [0, 0, 0, 0, 0, 0, 0, 0] ## intersection, contact, adjacency, above, below, left, right, coincidence 
    minx = max(x1, x3)
    miny = max(y1, y3)
    maxx = min(x2, x4)
    maxy = min(y2, y4)
    if x1 == x3 and y1 == y3 and x2 == x4 and y2 == y4:
        out[7]= 1
        return out
    if minx < maxx and miny < maxy:
        out[0] = 1
    else:
        if minx == maxx or miny == maxy:
            out[1] = 1
        else:
            out[2] = 1
        s1x = (x1 + x2)/2
        s1y = (y1 + y2)/2
        s2x = (x3 + x4)/2
        s2y = (y3 + y4)/2
        if s1x <= s2x:
            out[5] = 1
        else:
            out[6] = 1
        if s1y <= s2y:
            out[3] = 1
        else:
            out[4] = 1
    return out
    