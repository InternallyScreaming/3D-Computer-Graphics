import maya.cmds as cmds
import math

ZV = 0.000000000000000000001
worldOrigin = [0.0, 0.0, 0.0]

if 'MyWin' in globals():
    if cmds.window(MyWin, exists=True):
        cmds.deleteUI(MyWin, window=True)

MyWin = cmds.window(title='My UI', menuBar=True, widthHeight=(600,450), topLeftCorner=(100,100))

cmds.columnLayout( columnAttach=('left', 5), rowSpacing=10, columnWidth=500)
cmds.button( label='FIND INTERSECT', command='findIntersect()', width=(600))
cmds.setParent("..")
cmds.paneLayout()
cmds.textScrollList('uiPointList', numberOfRows=8, allowMultiSelection=False, height=(400))

cmds.showWindow(MyWin)

def findIntersect():
    selectedShapes = cmds.ls(selection=True)
    meshList = []
    lineVectorList = []
    
    for shape in selectedShapes:
        if(cmds.objectType(shape)=='transform'):
            childShape= cmds.listRelatives(shape, fullPath=True, shapes=True)
            if(cmds.objectType(childShape)=='mesh'):
                meshList.append(shape)
    
    if len(meshList) < 2:
        print "Not enough objects selected."
        return False
    elif len(meshList) > 2:
        print "Too many objects. Only two will be used."
        meshList=meshList[0:2]

    plane = meshList[0]
    test = meshList[1]

    lineVectorList = vertexFinder(plane)
    faceFinder(test, lineVectorList, worldOrigin)

def vertexFinder(object):
    vertexCount = cmds.polyEvaluate(object,vertex=True)
    meshTransform = cmds.xform(object, query=True, matrix=True, worldSpace=True)
    lineVector = []
    for vertex in range(0, vertexCount):
        vertexName = object + ".vt[" + str(vertex) + "]"
        vertexPosition = cmds.getAttr(vertexName)
        vertexPosition = list(vertexPosition[0])
        V = matrixMult(meshTransform, vertexPosition)
        lineVector.append(V)
    return lineVector

def faceFinder(object, lineVector, origin):
    faceCount = cmds.polyEvaluate(object, face=True)
    meshTransform = cmds.xform(object, query=True, matrix=True, worldSpace=True)
    intersectCount=1

    for face in range(0, faceCount):
        faceName = object +".f[" + str(face)+ "]"
        vertexList = cmds.polyInfo(faceName, faceToVertex=True)
        vertexIdx = str(vertexList[0]).split()
        vertexIdx = vertexIdx[2:]

        vtxA = cmds.getAttr(object + ".vt[" + vertexIdx[0] + "]")
        vtxB = cmds.getAttr(object + ".vt[" + vertexIdx[1] + "]")
        vtxC = cmds.getAttr(object + ".vt[" + vertexIdx[2] + "]")
        vtxD = cmds.getAttr(object + ".vt[" + vertexIdx[3] + "]")

        vtxA = list(vtxA[0])
        vtxB = list(vtxB[0])
        vtxC = list(vtxC[0])
        vtxD = list(vtxD[0])

        vtxA = matrixMult(meshTransform, vtxA)
        vtxB = matrixMult(meshTransform, vtxB)
        vtxC = matrixMult(meshTransform, vtxC)
        vtxD = matrixMult(meshTransform, vtxD)

        NV = getNormal(vtxA, vtxB, vtxC)
        planeEq = getPlaneEq(NV, vtxA)

        if planeEq == False:
            continue
        for i in range(0, len(lineVector)):
            LV = lineVector[i]
            LVx = LV[0]
            LVy = LV[1]
            LVz = LV[2]
            pI = [0.0, 0.0, 0.0]

            kValueA = (planeEq[0] * LVx)+(planeEq[1] * LVy)+(planeEq[2] * LVz) + planeEq[3]
            kValueB = (planeEq[0] * origin[0]) + (planeEq[1] * origin[1]) + (planeEq[2] * origin[2]) + planeEq[3]

            if(((kValueA>=0.0) and (kValueB>=0.0)) or ((kValueA<=0.0) and (kValueB<=0.0))):
                continue

            # Intersection is possible, so find t-value
            tValue = getTValue(planeEq, LV, origin)

            if tValue == False:
                continue
            
            pI[0] = LVx + (tValue * (origin[0] - LVx))
            pI[1] = LVy + (tValue * (origin[1] - LVy))
            pI[2] = LVz + (tValue * (origin[2] - LVz))

            isIntersectInCOOB = findTriangle(vtxA, vtxB, vtxC, pI)
            isItReallyInCOOB = findTriangle(vtxA, vtxD, vtxC, pI)

            Area = findFaceArea(vtxA, vtxB, vtxC)
            Distance = findDistance(LV, pI)
            Angle = findAngle(LV, pI, NV)

            if isIntersectInCOOB == False:
                if isItReallyInCOOB ==True:
                    printCubesAndInfo(pI, Area, NV, Distance, Angle, intersectCount)
                    intersectCount += 1
            elif isIntersectInCOOB == True:
                printCubesAndInfo(pI, Area, NV, Distance, Angle, intersectCount)
                intersectCount += 1

def createBetweenVector(pA, pB):
    vAB = [0,0,0]
    vAB[0] = pB[0] - pA[0]
    vAB[1] = pB[1] - pA[1]
    vAB[2] = pB[2] - pA[2]
    return vAB

def getNormal(vA, vB, vC):

    AB = createBetweenVector(vA, vB)
    AC = createBetweenVector(vA, vC)

    normV = getCross(AB, AC)
    normMag = getMagnitude(normV)

    normV[0] = normV[0]/normMag
    normV[1] = normV[1]/normMag
    normV[2] = normV[2]/normMag
    return normV

def getPlaneEq(normV, vX):

    A = normV[0]
    B = normV[1]
    C = normV[2]
    x = vX[0]
    y = vX[1]
    z = vX[2]

    D = x*A + y*B + z*C
    D = D * -1

    planeEq = [A,B,C,D]

    # Check if they are colinear
    if((abs(planeEq[0]) < ZV) and (abs(planeEq[1]) < ZV) and (abs(planeEq[2]) < ZV)):
        print("Error Points are Colinear")
        return False

    return planeEq

def getTValue(eQ, A, B):
    nomEq = 0.0
    denEq = 0.0

    denEq=(eQ[0]*(A[0]-B[0]))+(eQ[1]*(A[1]-B[1]))+(eQ[2]*(A[2]-B[2]))
    if(abs(denEq) < ZV):
        print "Denominator is Zero"
        return False
    
    nomEq = (eQ[0] * A[0]) + (eQ[1] * A[1]) + (eQ[2] * A[2]) + eQ[3]
    return(nomEq/denEq)

def matrixMult(Mtx, Pt):
    PtOut = [0.0, 0.0, 0.0, 0.0]
    PtIn = [Pt[0], Pt[1], Pt[2], 1]    # Convert to Homogeneous Point
    PtOut[0] =(Mtx[0]*PtIn[0])+(Mtx[4]*PtIn[1])+(Mtx[8]*PtIn[2])+(Mtx[12]*PtIn[3])
    PtOut[1] =(Mtx[1]*PtIn[0])+(Mtx[5]*PtIn[1])+(Mtx[9]*PtIn[2])+(Mtx[13]*PtIn[3])
    PtOut[2] =(Mtx[2]*PtIn[0])+(Mtx[6]*PtIn[1])+(Mtx[10]*PtIn[2])+(Mtx[14]*PtIn[3])
    PtOut[3] =(Mtx[3]*PtIn[0])+(Mtx[7]*PtIn[1])+(Mtx[11]*PtIn[2])+(Mtx[15]*PtIn[3])
    PtOut = PtOut[0:3]
    return(PtOut)

def getMagnitude(vec):
    magnitude = ((vec[0] ** 2) + (vec[1] ** 2) + (vec[2] ** 2)) ** 0.5
    return magnitude

def getDot(vec1, vec2):
    V1V2 = (vec1[0] * vec2[0]) + (vec1[1] * vec2[1]) + (vec1[2] * vec2[2])
    return V1V2

def getCross(vec1, vec2):
    cross = [0,0,0]
    cross[0] = (vec1[1] * vec2[2]) - (vec1[2] * vec2[1])
    cross[1] = (vec1[2] * vec2[0]) - (vec1[0] * vec2[2])
    cross[2] = (vec1[0] * vec2[1]) - (vec1[1] * vec2[0])
    return cross

#referenced the Barycentric Model that I got from this site
#http://blackpawn.com/texts/pointinpoly/?fbclid=IwAR3TdScX_OtPP8t38pWY64QYyUu1q2KMG4_3ZHCJcoidXYf3UnTvij1iPww
def findTriangle(A,B,C,P):
    BA = createBetweenVector(B,A)
    CA = createBetweenVector(C,A)
    PA = createBetweenVector(P,A)

    dotBABA = getDot(BA, BA)
    dotBACA = getDot(BA, CA)
    dotBAPA = getDot(BA, PA)
    dotCACA = getDot(CA, CA)
    dotCAPA = getDot(CA, PA)

    revDenom = 1 / (dotBABA * dotCACA - dotBACA * dotBACA)
    u = (dotCACA * dotBAPA - dotBACA * dotCAPA) * revDenom
    v = (dotBABA * dotCAPA - dotBACA * dotBAPA) * revDenom

    if (u >= 0) and (v >= 0) and (u + v < 1):
        return True
    else:
        return False

def findFaceArea(A,B,C):
    AB = createBetweenVector(A,B)
    AC = createBetweenVector(A,C)
    CP = getCross(AB, AC)
    area = getMagnitude(CP)
    return area

def findDistance(A, B):
    Line = createBetweenVector(B, A)
    distance = getMagnitude(Line)
    return distance

def findAngle(pt1, pt2, normal):
    line = createBetweenVector(pt1, pt2)
    numerator = getDot(normal, line)

    magLine = getMagnitude(line)
    magNorm = getMagnitude(normal)

    Theta = math.cos(numerator/(magLine*magNorm))
    return Theta

def printCubesAndInfo(pI, faceArea, NV, distance, angle, intersectCount):
    cmds.polyCube(width=0.1, height=0.1, depth=0.1)
    cmds.move(pI[0], pI[1], pI[2])
    pI[0] = round(pI[0], 2)
    pI[1] = round(pI[1], 2)
    pI[2] = round(pI[2], 2)
    faceArea = round(faceArea, 2)
    distance =  round (distance, 2)
    angle = round(angle, 2)

    ptText = "Int. Pt.: [" + str(intersectCount) + "] [" + str(pI[0]) + ", " + str(pI[1]) + ", " + str(pI[2]) +"] Face Area: " + str(faceArea) + " NV: [" + str(NV[0]) + ", " + str(NV[1]) + ", " + str(NV[2]) + "] Distance: " + str(distance) + " Angle: " + str(angle) + " rads"
    cmds.textScrollList('uiPointList', edit=True, append=[ptText])








