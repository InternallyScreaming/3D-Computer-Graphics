import maya.cmds as cmds
import random as rnd

if 'myWin' in globals():
    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin, window=True)

if 'nextChainId' not in globals():
    nextChainId = 1000

myWin = cmds.window(title="Chain Generator", menuBar=True,  topLeftCorner=(100,1000))

cmds.menu(l="Basic Options")
cmds.menuItem(l="New Scene", command=('cmds.file(new=True, force=True)'))
cmds.menuItem(l="Delete Selected", command=('cmds.delete()'))

cmds.frameLayout(collapsable=True, l="Chain", width=475, height=140)

cmds.gridLayout(ch = 25, cw = 75, nc = 4, ag = True)
cmds.text('Title', l='Link Shapes')
cmds.radioCollection('linkTypes')
cmds.radioButton('regularLink', l="Regular", cl = 'linkTypes', da=1, sl = True)
cmds.radioButton('circleLink', l="Circle", cl = 'linkTypes', da=2)
cmds.radioButton('squareLink', l="Square", cl = 'linkTypes', da=3)
cmds.text('')
cmds.radioButton('diamondLink', l="Diamond", cl = 'linkTypes', da=4)
cmds.radioButton('octagonLink', l="Octagon", cl = 'linkTypes', da=5)
cmds.radioButton('eightShapeLink', l="Eight", cl = 'linkTypes', da=6)
cmds.setParent( '..' )

cmds.columnLayout(rs = 5)
cmds.radioButtonGrp('SpawnAs', l = 'Spawn Chain', nrb = 2, la2 = ['Straight', 'Curve'], sl = 1)
cmds.checkBoxGrp('merge', l = "Merge Chain Links")
cmds.intSliderGrp('chainLength', l="Chain Length", f=True, min=1, max = 100, fmx = 5000, value=2)
cmds.intSliderGrp('linkSize', l="Link Size", f=True, min=1, max=10, fmx = 200, value=1)
cmds.intSliderGrp('linkThickness', l="Link Thickness", f=True, min=1, max=10, value=5)
cmds.intSliderGrp('linkSlack', l="Link Slack", f=True, min=0, max=10, value=0, step = .1)
cmds.colorSliderGrp('chainColour', l="Colour", hsv=(120, 1, 1))
cmds.button(l="Create Chain", command=('createChain()'))
cmds.setParent( '..' )
cmds.setParent( '..' )

cmds.showWindow(myWin)

def createChain():
    linkType = cmds.radioCollection('linkTypes', q = True, sl = True)
    spawnType  = cmds.radioButtonGrp('SpawnAs', q = True, sl = True)
    chainLength = cmds.intSliderGrp('chainLength',  q=True, v=True)
    linkSize = cmds.intSliderGrp('linkSize', q=True, v=True)
    linkThickness = cmds.intSliderGrp('linkThickness', q=True, v=True)
    combine = cmds.checkBoxGrp('merge', q = True, v1 = True)

    SIZE = linkSize
    THICK = linkThickness * .05
    MOD = Tightness(linkType, linkThickness)

    #Load Curve Warp plug in if it is not already loaded in
    if not cmds.pluginInfo( 'curveWarp', q=True, l=True ):
        cmds.loadPlugin( 'curveWarp', qt=True)

    #If the users chooses to spawn on a curve
    if spawnType == 2:
        selectedCurve = cmds.ls(selection=True)
        curveList = []

        #save all curves to a curve list
        for curve in selectedCurve:
            if(cmds.objectType(curve)=='transform'):
                childShape=cmds.listRelatives(curve, fullPath=True, shapes=True)
                if(cmds.objectType(childShape)=='nurbsCurve' or cmds.objectType(childShape)=='bezierCurve'):
                    curveList.append(curve)

        #Return false if no curve was found
        if len(curveList) < 1:
            print "A curve was not selected"
            return False
        #If the curve list is greater than 1, the first curve will be used
        elif len(curveList) > 1:
            print "Too many objects. The first curve selected will be used."
            curveList=curveList[0]

        #Return false if the user chooses to not have the chain links merged
        #all links must be merged together for curve warp to work
        if combine == False:
            print "Chain links must be combined to spawn chain on a curve"
            return False

    global nextChainId
    NSTMP = "Chain" + str(nextChainId)
    nextChainId = nextChainId + 1

    cmds.select(clear=True)
    cmds.namespace(set=":")
    cmds.namespace(add=NSTMP)
    cmds.namespace(set=NSTMP)

    #loop through the chain length and spawns each link individually
    for i in range(0, chainLength):
        offset = SIZE * (i * MOD)
        if i % 2 == 1:
            angle = 0
        else:
            angle = 90
        
        # regular link shape
        if linkType == "regularLink":
            regularLink(angle, offset, SIZE, THICK, NSTMP)
            cmds.select(NSTMP + ":Link1_")
            cmds.rename("Link1")

        # circle link shape
        elif linkType == "circleLink":
            circleLink(angle, offset, SIZE, THICK, NSTMP)

        # square link shape
        elif linkType == "squareLink":
            squareLink(angle, 45, offset, SIZE, THICK, NSTMP)

        # diamond link shape, uses square function just rotates a square by 45 deg to make a diamond
        elif linkType == "diamondLink":
            squareLink(angle, 0, offset, SIZE, THICK, NSTMP)

        # octagon link shape
        elif linkType == "octagonLink":
            octLink(angle, offset, SIZE, THICK, NSTMP)

        elif linkType == "eightShapeLink":

            eightLink(angle, offset, SIZE, THICK, NSTMP)
            cmds.select(NSTMP + ":Link1_")
            cmds.rename("Link1")
    
    #if the chain is spawned straight
    if spawnType == 1:
        StraightSpawn(NSTMP)
    #if the chain is spawned on a curve
    elif spawnType == 2:
        CurveSpawn(NSTMP, curveList[0])

def regularLink(rot_X, move_X, SIZE, THICK, nsTmp):
    Idx1 = 5
    Idx2 = 8

    #creates a torus
    cmds.polyTorus(sa=8, sh = 8, sr = THICK, n = "Link1_")
    cmds.rotate(90, 0, 0)
 
    #select a range of faces
    for i in range(9):
        facet = nsTmp + ":Link1_.f[" + str(Idx1) + ":" + str(Idx2) + "]"

        if i == 0:
            cmds.select(nsTmp + ":Link1_" + ".f[0]")
        else:
            cmds.select(facet, add = True)

            Idx1 = Idx1 + 8
            if i == 7:
                Idx2 = Idx2 + 7
            else:
                Idx2 = Idx2 + 8
    
    #extrudes the faces and moves them to the left, thus making the elongated shape
    cmds.polyExtrudeFacet(kft = True, ws = True, t = [2,0,0])
    cmds.delete(ch=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

    cmds.select(nsTmp+":Link1_")
    cmds.xform(cp=True)
    cmds.scale(SIZE, SIZE, SIZE)
    cmds.move(move_X,0,0)
    cmds.rotate(rot_X,0,0)
    cmds.polySmooth()

def circleLink(rot_X, move_X, SIZE, THICK, nsTmp):
    cmds.polyTorus(sr = THICK, n = "Link1")
    cmds.move(move_X,0,0)
    cmds.rotate(rot_X,0,0)
    cmds.scale(SIZE, SIZE, SIZE)

def squareLink(rot_X, rot_Y, move_X, SIZE, THICK, nsTmp):
    cmds.polyTorus(sa = 4, sr = THICK, n = "Link1")
    cmds.rotate(rot_Y, rotateY = True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
    cmds.rotate(rot_X, rotateX = True)
    cmds.move(move_X,0,0)
    cmds.scale(SIZE, SIZE, SIZE)    

def octLink(rot_X, move_X, SIZE, THICK, nsTmp):
    cmds.polyTorus(sa = 8, sh = 8, sr = THICK, n = "Link1")
    cmds.move(move_X,0,0)
    cmds.rotate(rot_X, 0 ,0)
    cmds.scale(SIZE, SIZE, SIZE)

def eightLink(rot_X, move_X, SIZE, THICK, nsTmp):
    Idx1 = 5
    Idx2 = 8

    cmds.polyTorus(sa=8, sh = 8, sr = THICK, n = "Link1_")
    cmds.rotate( '90deg', 0, 0 )
    
    #select a range of faces
    for i in range(9):
        facet = nsTmp + ":Link1_.f[" + str(Idx1) + ":" + str(Idx2) + "]"

        if i == 0:
            cmds.select(nsTmp + ":Link1_" + ".f[0]")
        else:
            cmds.select(facet, add = True)

            Idx1 = Idx1 + 8
            if i == 7:
                Idx2 = Idx2 + 7
            else:
                Idx2 = Idx2 + 8

    cmds.polyExtrudeFacet(kft = True, ws = True, t = [1,0,0])
    cmds.polyExtrudeFacet(kft = True, ws = True, t = [1,0,0])
    
    #select the vertexes and move them to make the 8 shape
    num = 44
    for i in range(7):
        if i == 0:
            cmds.select(nsTmp + ':Link1_.vtx[' + str(40) + ':' + str(41) + ']')
        else:
            cmds.select(nsTmp + ':Link1_.vtx[' + str(num) + ']', add=True)
            num += 2
    cmds.move(0, -0.8, 0, r=True)

    num = 45
    for i in range(7):
        if i == 0:
            cmds.select(nsTmp + ':Link1_.vtx[' + str(42) + ':' + str(43) + ']')
        else:
            cmds.select(nsTmp + ':Link1_.vtx[' + str(num) + ']', add=True)
            num += 2
    cmds.move(0, 0.8, 0, r=True)  

    cmds.delete(ch=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
    
    cmds.select(nsTmp + ":Link1_")
    cmds.xform(cp=True)
    cmds.scale(SIZE, SIZE, SIZE)
    cmds.move(move_X,0,0)
    cmds.rotate(rot_X,0,0)
    cmds.polySmooth()

def StraightSpawn(nsTmp):
    Merge(nsTmp)

def CurveSpawn(nsTmp, CURVE):
    Merge(nsTmp)
    cmds.createCurveWarp(nsTmp,CURVE)
    cmds.delete(ch=True)
    cmds.xform(cp=True)

def Merge(nsTmp):
    combine = cmds.checkBoxGrp('merge', q = True, v1 = True)
    rgb = cmds.colorSliderGrp('chainColour', q=True, rgbValue=True)
    
    if combine == True:
        myShader = cmds.shadingNode('lambert', asShader=True, name="blckMat")
        cmds.setAttr(nsTmp+":blckMat.color",rgb[0],rgb[1],rgb[2], typ='double3')
        
        cmds.polyUnite((nsTmp+":*"), n=nsTmp, ch=False)
        cmds.delete(ch=True)
        
        cmds.hyperShade(assign=(nsTmp+":blckMat"))
        cmds.namespace( removeNamespace=":"+nsTmp, mergeNamespaceWithParent = True)
    else:
        myShader = cmds.shadingNode('lambert', asShader=True, name="blckMat")
        cmds.setAttr(nsTmp+":blckMat.color",rgb[0],rgb[1],rgb[2], typ='double3')

        cmds.group((nsTmp+":*"), n=nsTmp)
        
        cmds.hyperShade(assign=(nsTmp+":blckMat"))
        cmds.namespace( removeNamespace=":"+nsTmp, mergeNamespaceWithParent = True)

def Tightness(linkType, linkThickness):
    linkSlack = cmds.intSliderGrp('linkSlack', q=True, v=True)

    if linkType == "regularLink":
        linkSlack = linkSlack * .1
        MOD = ((3.9-linkSlack) - (linkThickness * .1))
    elif linkType == "circleLink":
        linkSlack = linkSlack * .02
        MOD  = ((1.95-linkSlack) - (linkThickness * .1))
    elif linkType == "squareLink":
        linkSlack = linkSlack * .015
        MOD =  ((1.34-linkSlack) - (linkThickness * .06))
    elif linkType == "diamondLink":
        linkSlack = linkSlack * .014
        MOD = ((1.9-linkSlack) - (linkThickness * .1))
    elif linkType == "octagonLink":
        linkSlack = linkSlack * .016
        MOD = ((1.85-linkSlack) - (linkThickness * .087))
    elif linkType == "eightShapeLink":
        linkSlack = linkSlack * .1
        MOD = ((3.9-linkSlack) - (linkThickness * .1))
    return MOD
