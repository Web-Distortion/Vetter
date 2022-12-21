import os
import sys
import json

def isTXT(filename):
    fileType = os.path.splitext(filename)[-1]
    if fileType == ".txt" and filename != "all.txt" and filename != "merge.txt":
        return True
    else:
        return False
    

def merge(dirPath):
    files = os.listdir(dirPath)
    files = list(filter(isTXT, files))
    if len(files) == 0:
        return
    firstFile = dirPath + "jsonlayer_0" + ".skp.txt"
    with open(firstFile, 'r') as ff:
        jsonObjs = json.loads(ff.read())

    for i in range(1, len(files)):
        filePath = dirPath + "jsonlayer_" + str(i) + ".skp.txt"
        print(filePath)
        with open(filePath, 'r') as fread:
            commands = json.loads(fread.read())["commands"]
            jsonObjs["commands"] += commands
    outfile = dirPath + "all.txt"
    f = open(outfile, 'w')
    f.write(json.dumps(jsonObjs, indent=2))
    f.close()

def combineTextBlob(dirPath, txtPath):
    filePath = dirPath + "all.txt"
    f = open(filePath, 'r')
    jsonObj = json.loads(f.read())
    commands = jsonObj["commands"]
    f.close()
    combineList = []
    for cmd in commands:
        if len(combineList) == 0:
            combineList.append(cmd)
        else:
            if cmd["command"] == "DrawTextBlob":
                if combineList[-1]["command"] == "DrawTextBlob":
                    try:
                        if cmd["runs"][0]["font"]["textSize"] == combineList[-1]["runs"][0]["font"]["textSize"]:
                            position1 = cmd["shortDesc"].strip(' []').split(" ")
                            position2 = combineList[-1]["shortDesc"].strip(' []').split(" ")
                            position2[0] = min(float(position2[0]), float(position1[0]))
                            position2[1] = min(float(position2[1]), float(position1[1]))
                            position2[2] = max(float(position2[2]), float(position1[2]))
                            position2[3] = max(float(position2[3]), float(position1[3]))
                            combineList[-1]["shortDesc"] = " [" + " ".join([str(num) for num in position2]) + "]"
                        else:
                            combineList.append(cmd)
                    except:
                        combineList.append(cmd)


                else:
                    combineList.append(cmd)
            else:
                combineList.append(cmd)
    jsonObj["commands"] = combineList
    f = open(txtPath, 'w')
    f.write(json.dumps(jsonObj, indent=2))
    f.close()





if __name__ == "__main__":
    dirPath = sys.argv[1]
    txtPath = sys.argv[2]
    merge(dirPath)
    combineTextBlob(dirPath, txtPath)