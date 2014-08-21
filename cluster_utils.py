# -*- coding: utf-8 -*-
"""
Created on Wed Aug 06 23:44:46 2014

@author: Sheldon
"""

def sameRect(rect, bounds):
    same = True
    for i in range(len(rect)):
        if not rect[i][0] == bounds[i][0] or not rect[i][1] == bounds[i][1]:
            same = False
    return same
    
def clearRect(h2, incd, rect, thresh):
    nx = len(h2)
    ny = len(h2[0])

    xlo = rect[0][0]
    xhi = rect[2][0]
    ylo = rect[0][1]
    yhi = rect[1][1]

    xlo2 = xlo-1 if xlo>0 else 0
    xhi2 = xhi+1 if xhi<nx else nx
    ylo2 = ylo-1 if ylo>0 else 0
    yhi2 = yhi+1 if yhi<ny else ny
        
    for j in range(ylo2, yhi2):
        nearest = findNearest(rect, (xlo2, j))    
        if incd[nearest[0], nearest[1]] and h2[xlo2, j] > thresh:
            incd[xlo2, j] = 1
    for j in range(xlo2, min(xhi2+1, nx)):
        iy = min(yhi2, ny-1)
        nearest = findNearest(rect, (j, iy))    
        if incd[nearest[0], nearest[1]] and h2[j, iy] > thresh:
#            print "UL: ", j, yhi2
            incd[j, iy] = 1
    for j in range(ylo2, yhi2):
        ix = min(xhi2, nx-1)
        nearest = findNearest(rect, (ix, j))    
        if incd[nearest[0], nearest[1]] and h2[ix, j] > thresh:
            incd[ix, j] = 1
    for j in range(xlo2+1, xhi2):
        nearest = findNearest(rect, (j, ylo2))
        if incd[nearest[0], nearest[1]] and h2[j, ylo2] > thresh:
            incd[j, ylo2] = 1
    
    return ((xlo2, ylo2), (xlo2, yhi2), (xhi2, yhi2), (xhi2, ylo2))

def findNearest(rect, p):
    ix = p[0]
    iy = p[1]
    xlo = rect[0][0]
    xhi = rect[2][0]
    ylo = rect[0][1]
    yhi = rect[1][1]
    
    nearx = ix
    neary = iy
    if ix <= xlo: 
        nearx = xlo
    elif ix >= xhi: 
        nearx = xhi

    if iy <= ylo:
        neary = ylo
    elif iy >= yhi:
        neary = yhi
        
    return (nearx, neary)
    
def drawBoundary(incd):
    incd2 = list()
    for x in range(len(incd)):
        for y in range(len(incd[0])):
            if incd[x,y]: incd2.append((x,y))
    t = zip(*incd2)
    yvert = min(t[1])
    idx = t[1].index(yvert)
    xvert = t[0][idx]    

    path = [(xvert, yvert)]
    
    return findMove(incd, path)

def findMove(incd, path):

    nx = len(incd)
    ny = len(incd[0])
    allowed = {"left":("down", "left", "up"), 
               "up": ("left", "up", "right"),
                "right": ("up", "right", "down"),
                "down": ("right", "down", "left")}
                
    lastMove = "up"

    [x, y] = path[0]
    x0 = y0 = -1
    while x0 != x or y0 != y:  
        moved = False
        for m in allowed[lastMove]:
#            print m
            if not moved:
                if m == "left":
                    if x>0 and y<ny and incd[x-1, y]:    
#                        print "found : ",m,x0,y0,x,y
                        path.append((x-1, y))
                        lastMove = "left"
                        moved = True
                elif m == "up":
                    if y<ny and incd[x, y]:
#                        print "found : ",m,x0,y0,x,y
                        path.append((x, y+1))
                        lastMove = "up"
                        moved = True
                elif m == "right":
                    if x<nx and incd[x, y-1]:
#                        print "found : ",m,x0,y0,x,y
                        path.append((x+1, y))
                        lastMove = "right"
                        moved = True
                elif m == "down":
                    if y>0 and x>0 and incd[x-1, y-1]:
#                        print "found : ",m,x0,y0,x,y
                        path.append((x, y-1))
                        lastMove = "down"
                        moved = True
                    
        (x0, y0) = path[0]
        (x, y) = path[-1]
    
    return path
