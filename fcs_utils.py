# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 11:05:14 2014

@author: Sheldon
"""
import numpy as np
from matplotlib import path
import matplotlib.patches as patches


def read_fcs(fname):
    f=open(fname,'r')
    header=f.read(64)
    start=header[15:18]
    stop=header[22:26]
    dstart=header[30:34]
    blank=f.read(int(start)-64)
    header_main=f.read(int(stop)-int(start))

    #blank=f.read(int(dstart)-int(stop))
    separ=header_main[0]
    vals=header_main[1:].split(separ)
    kvarg=dict ()
    for i in range(len(vals)/2):
        kvarg[vals[i]]=vals[i+1]
    
    f.seek(int(dstart))
    x=np.fromfile(f,dtype=np.uint8)        
    
    y=[]
    for i in range(len(x)):
        if i%2 == 0:
            for j in [0,1]:
                t = x[i]*256+x[i+j]
            y.append(10**(4.*t/1024.))
#            y.append(t)
    dat=[]
    for i in range(len(y)):
        if i%7 == 0:
            t=[]
            for j in range(7):
                t = t + [y[i+j]]
            dat.append(t)
    f.close()
    return [kvarg, dat]

def get_channel(kvarg):
    chan = []
    for i in range(1,8):
        k = "$P{0}N".format(i)
        chan.append(kvarg[k])
    return chan       

def get_header(fname):
    f=open(fname,'r')
    header=f.read(64)
    start=header[15:18]
    stop=header[22:26]
    dstart=header[30:34]
    blank=f.read(int(start)-64)
    header_main=f.read(int(stop)-int(start))

    #blank=f.read(int(dstart)-int(stop))
    separ=header_main[0]
    vals=header_main[1:].split(separ)
    kvarg=dict()
    for i in range(len(vals)/2):
        kvarg[vals[i]]=vals[i+1]

    return kvarg

def fcs_hist(n,bins):
    # get the corners of the rectangles for the histogram
    left = np.array(bins[:-1])
    right = np.array(bins[1:])
    bottom = np.zeros(len(left))
    top = bottom + n
    nrects = len(left)
    
    nverts = nrects*(1+3+1)
    verts = np.zeros((nverts, 2))
    codes = np.ones(nverts, int) * path.Path.LINETO
    codes[0::5] = path.Path.MOVETO
    codes[4::5] = path.Path.CLOSEPOLY
    verts[0::5,0] = left
    verts[0::5,1] = bottom
    verts[1::5,0] = left
    verts[1::5,1] = top
    verts[2::5,0] = right
    verts[2::5,1] = top
    verts[3::5,0] = right
    verts[3::5,1] = bottom
    
    barpath = path.Path(verts, codes)
    patch = patches.PathPatch(barpath, facecolor='green', edgecolor='black', alpha=0.5)
    
    return patch
    
def fcs_manhattan(n,bins,smooth=False):
    left = np.array(bins[:-1])
    right = np.array(bins[1:])
    bottom = np.zeros(len(left))
    top = bottom + n
    
    nrects = len(left)
    
    nverts = nrects*(1+3)
    verts = np.zeros((nverts, 2))
    verts[0::4,0] = left
    verts[0::4,1] = bottom
    verts[1::4,0] = left
    verts[1::4,1] = top
    verts[2::4,0] = right
    verts[2::4,1] = top
    verts[3::4,0] = right
    verts[3::4,1] = bottom

    from scipy.interpolate import interp1d
    if smooth:
        x = np.append([verts[0,0]], verts[2::4,0], 0)
        y = np.append([0], top)
        f = interp1d(x, y, kind='cubic')
        xnew = np.linspace(bins[0], bins[-1], 3*len(bins))
        ynew = f(xnew)
        return np.array(zip(xnew, ynew))
    else:
        return verts
