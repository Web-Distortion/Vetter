import os
import sys
import json
import collections
from compare import nodeComparison
from relationship import relationship
import numpy as np

def getCoords(node):
    if node["command"] == "DrawRect":
        shortDesc = node["shortDesc"]
        shortDesc = shortDesc[2:-1]
        coords = list(map(float, shortDesc.split(" ")))
    elif node["command"] == "DrawImageRect":
        shortDesc = node["shortDesc"]
        shortDesc = shortDesc[2:-1]
        coords = list(map(float, shortDesc.split(" ")))
    elif node["command"] == "DrawTextBlob":
        shortDesc = node["shortDesc"]
        shortDesc = shortDesc[2:-1]
        coords = list(map(float, shortDesc.split(" ")))
    elif node["command"] == "DrawRRect":
        coords = node["coords"][0]
                
    return coords

def getArea(coords):
    [x1, y1, x2, y2] = coords
    return (x2 - x1) * (y2 - y1)

def isIn(c1, c2):
    [x1, y1, x2, y2] = c1
    [x3, y3, x4, y4] = c2
    if x1 >= x3 and x2  <=x4 and y1 >= y3 and y2 <= y4:
        if x1 == x3 and x2 == x4 and y1 == y3 and y2 == y4:
            return False
        else:
            return True
    else:
        return False

def buildGraph(commmands):
    nodes = []
    root = {
        "command": "DrawRect",
        "visible": True,
        "coords": [ -100000, -100000, 100000, 100000 ],
        "paint": {
        "antiAlias": True,
        "color": [ 255, 153, 153, 153 ],
        "filterQuality": "low"
        },
        "shortDesc": " [-100000 -100000 100000 100000]"
    }
    nodes.append(root)
    for command in commmands:
        if command["command"] == "DrawRect" or command["command"] == "DrawTextBlob" or command["command"] == "DrawImageRect" or command["command"] == "DrawRRect":
            nodes.append(command)
    edges = [[] for _ in range(len(nodes))]
    for i in range(1, len(nodes)):
        minj = -1
        minArea = 100000000000000
        if nodes[i]["command"] == "DrawRect":
            shortDesc = nodes[i]["shortDesc"]
            shortDesc = shortDesc[2:-1]
            coords1 = list(map(float, shortDesc.split(" ")))
        elif nodes[i]["command"] == "DrawImageRect":
            shortDesc = nodes[i]["shortDesc"]
            shortDesc = shortDesc[2:-1]
            coords1 = list(map(float, shortDesc.split(" ")))
        elif nodes[i]["command"] == "DrawTextBlob":
            shortDesc = nodes[i]["shortDesc"]
            shortDesc = shortDesc[2:-1]
            coords1 = list(map(float, shortDesc.split(" ")))
        elif nodes[i]["command"] == "DrawRRect":
            coords1 = nodes[i]["coords"][0]
        elif nodes[i]["command"] == "DrawPath":
            edges[0].append(i)
            continue
        else:
            continue

        for j in range(i):
            if nodes[j]["command"] == "DrawRect":
                shortDesc = nodes[j]["shortDesc"]
                shortDesc = shortDesc[2:-1]
                coords2 = list(map(float, shortDesc.split(" ")))
            elif nodes[j]["command"] == "DrawImageRect":
                shortDesc = nodes[j]["shortDesc"]
                shortDesc = shortDesc[2:-1]
                coords2 = list(map(float, shortDesc.split(" ")))
            elif nodes[j]["command"] == "DrawTextBlob":
                shortDesc = nodes[j]["shortDesc"]
                shortDesc = shortDesc[2:-1]
                coords2 = list(map(float, shortDesc.split(" ")))
            elif nodes[j]["command"] == "DrawRRect":
                coords2 = nodes[j]["coords"][0]
            else:
                continue
            if isIn(coords1, coords2):
                area = getArea(coords2)
                if area < minArea:
                    minArea = area
                    minj = j

        if minj != -1:
            edges[minj].append(i)
        else:
            f = open("errorlog.txt", 'w')
            f.write(json.dumps(nodes[i]))
            f.write('\n')
            f.close()    

    return edges, nodes

def generateKernel(edges, nodes):
    kernel = [np.array([0, 0, 0, 0, 0, 0, 0, 0]) for i in range(len(nodes))]
    for level in edges:
        for i in level:
            c1 = getCoords(nodes[i])
            for j in level:
                if i == j:
                    continue
                else:
                    c2 = getCoords(nodes[j])
                    kernel[i] += np.array(relationship(c1, c2))
    return kernel



                    


    

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("format error!")
        exit(0)
    filename1 = sys.argv[1]
    filename2 = sys.argv[2]
    outfile = sys.argv[3]
    f = open(outfile, 'w')
    f1 = open(filename1, 'r')
    f2 = open(filename2, 'r')
    cmds1 = json.loads(f1.read())["commands"]
    cmds2 = json.loads(f2.read())["commands"]
    edges1, nodes1 = buildGraph(cmds1)
    edges2, nodes2 = buildGraph(cmds2)
    # kernel = generateKernel(nodes1, nodes2)
    kernel1 = generateKernel(edges1, nodes1)
    kernel2 = generateKernel(edges2, nodes2)
    f.write(str(len(nodes1)) + ' ' + str(len(nodes1)-1))
    f.write("\n")

    for i in range(len(edges1)):
        for j in range(len(edges1[i])):
            f.write(str(i) + ' ' + str(edges1[i][j]))
            f.write('\n')
    f.write('\n')
    f.write(str(len(nodes2)) +  ' ' + str(len(nodes2)-1))
    f.write('\n')

    for i in range(len(edges2)):
        for j in range(len(edges2[i])):
            f.write(str(i) + ' ' + str(edges2[i][j]))
            f.write('\n')
    f.write('\n')

    for line in kernel1:
        f.write(" ".join([str(num) for num in line]))
        f.write('\n')
    f.write('\n')
    for line in kernel2:
        f.write(" ".join([str(num) for num in line]))
        f.write('\n')

    f.close()

    
