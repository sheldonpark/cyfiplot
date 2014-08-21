# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 00:03:01 2014

@author: Sheldon

Displays all possible combinations of scatter plots from fcs.dat

"""
import os
from flask import Flask, session, render_template, redirect, url_for, request
import numpy as np
import matplotlib
from matplotlib import gridspec
from matplotlib.pyplot import *
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from mpld3 import *
from mpld3 import plugins, utils
from mpld3.plugins import *
import ujson
from cluster_utils import *
from fcs_utils import read_fcs, fcs_manhattan, get_channel
from LinkedDragPlugin import *
from LinkedLinePlugin import *
from LinkedView import *
from LinkedView2 import *
from pymongo import MongoClient
from bson.objectid import ObjectId
import FlowCytometryTools as fctools
from FlowCytometryTools import FCMeasurement as fcmea

MAX_NDAT = 2000
MIN_NDAT = 10**6

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "c:/Users/Sheldon/IntDev/flask/temp"
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.secret_key = 'aklfkja;slirqjw;elkq'  # os.urandom(24)
client = MongoClient()
db = client.flowcy

@app.route('/test',methods=['GET','POST'])
def test():
    if request.method == 'POST':
        print "Args: ", request.args
        print "body: ", request.form
        print request.files['upfile']
        return render_template('cyfi-test.html')
    else:
        print "NOT POST"

@app.route('/')
def index():
    return redirect(url_for('form'))

@app.route('/form')
def form():
    return render_template('cyfi4.html')

@app.route("/plot", methods=['GET','POST'])
def plot():
    if request.method == 'POST':
##    if False:
        print "inside plot post"
        lis = request.files.getlist('upfile[]')
        names = []
        pids = []
        for f in lis:
            try:
                fname = "f" + str(int(np.random.random()*10**10))     
                fname = app.config['UPLOAD_FOLDER'] + "/" + fname
                f.save(fname)
#                [header, fdat] = read_fcs(fname) # header = kvarg
                header, fdat = fctools.parse_fcs(fname, 
                                      meta_data_only=False, 
                                      output_format='ndarray', 
                                      reformat_meta=True)
                s = fcmea(ID='mysample', datafile=fname)
                channel = s.channel_names
                print "channel: ", channel
                os.remove(fname)
                print "removed file"
                fobj = dict()
                fobj['filename'] = f.filename
                print "filename: ", f.filename
#                fobj['header'] = str(header)
#                print "header:", header
                fobj['data'] = fdat.tolist()
                pid = db.fcdata_file.insert(fobj)
                print "pid: ", pid
                pids.append(pid)
                names.append(f.filename)
            except:
                print "error reading file"
                continue
       
        dat = dict()
        dat['count'] = len(names)
        print "nfiles >> ", len(lis)
        dat['filenames'] = names
        dat['pids'] = pids
#        chan = get_channel(header)
        dat['channels'] = channel
        print "channels: ", channel
        pid = db.fcdata.insert(dat)
        print "pid", str(pid)
        
        session['pid'] = str(pid)
        session['channels'] = channel
        session['filenames'] = names

    return redirect(url_for('display'))
#    return redirect(url_for('display'))
    
@app.route("/display", methods=['GET', 'POST'])    
def display():
    pid = session['pid']
    print "pid in display: ", pid
    sel = db.fcdata.find({'_id':ObjectId(pid)}).next()
    print "sel: ", type(sel), sel.keys()
    pids = sel['pids']
    print "retrieved pid: ", len(pids)
    names = sel['filenames']
    channel = sel['channels']
    print "retrieved files: ", len(pids)
    first = True

# read data
    forside = []
    for p in pids:
        f = db.fcdata_file.find({'_id': p}).next()
        fdat = f['data']
        
        ndarray = np.array(fdat) # ndarray = fdat
        ndat = len(ndarray)
        if ndat < MIN_NDAT: pass
        print "found file .. "
    
#        x = np.log10(ndarray[:MAX_NDAT,0])
#        y = np.log10(ndarray[:MAX_NDAT,1])
        x = ndarray[:MAX_NDAT, 0]
        y = ndarray[:MAX_NDAT, 1]
        xy = np.array(zip(x, y))
        forside.append([x, y])
        
        xmax = max(x); xmin = 0
        ymax = max(y); ymin = 0
#        xmax, xmin, ymax, ymin = [4, 0, 4, 0]
        
#        dx = 0.1; dy = 0.1
#        nx = int((xmax-xmin)/dx) + 1
#        ny = int((ymax-ymin)/dy) + 1
        nx = 40; dx = float(xmax-xmin)/nx; nx += 1
        ny = 40; dy = float(ymax-ymin)/ny; ny += 1
        print "dx, dy", dx, dy

        if first: # define a preliminary gate based on the scatter plot of first file
            first = False
            h2 = np.zeros((nx, ny))
            for i in range(len(xy)):
                ix = int(xy[i,0]/dx)
                iy = int(xy[i,1]/dy)
                try:
                    h2[ix, iy] = h2[ix, iy] + 1
                except:
#                    print "error binning: ", ix, iy
                    pass

            peak = -1; ipeak = jpeak = 0
            for i in range(len(h2)):
                for j in range(len(h2[0])):
                    if  h2[i,j] > peak:
                        peak = h2[i,j]
                        ipeak = i
                        jpeak = j
        
            thresh = 0.1 * peak
            rect = ((ipeak, jpeak), (ipeak, jpeak), (ipeak, jpeak), (ipeak, jpeak))
            bounds = ((0, 0), (0, ny), (nx, ny), (nx, 0))
            incd = np.zeros((nx, ny)) # bins included in the cluster
            incd[ipeak, jpeak] = 1
            ct = 0
            while not sameRect(rect, bounds):
                #    print "Count : %d" % ct, rect, bounds
                rect = clearRect(h2, incd, rect, thresh) # update the included bins
                ct = ct + 1

    forside = np.array(forside)
    print "forside: ", len(forside), len(forside[0]), len(forside[0][0])
    [x, y] = [forside[0][0], forside[0][1]]

# plot forward vs. side        
    fig = plt.figure()
    fig.set_size_inches(8,8)
    gs = gridspec.GridSpec(3,1)
    ax = []
    ax.append(plt.subplot(gs[:2,:]))
    ax.append(plt.subplot(gs[2,:]))

    scatline = ax[0].plot(x, y, 'k', lw=1, alpha=0.)
    scatpts = ax[0].plot(x, y, 'ko', markersize=1)
    #print "lines: ", len(lines), lines
    ax[0].set_title("Forward vs. Side Scatter (Displaying 2000 Entries)")
        
# define and draw initial gate
    bounds = drawBoundary(incd)
    print "bounds: ", bounds
    codes = [Path.MOVETO]
    for i in range(1,len(bounds)-1):
        codes.append(Path.LINETO)
    codes.append(Path.CLOSEPOLY)

    npt = len(bounds)/5 # draw a hexagon
    print "ntp: ", npt
    a = bounds[:-1:npt]; a.append(bounds[-1])
    b = codes[:-1:npt]; b.append(codes[-1])
    print "a, b", a, b

    xcoor = np.linspace(xmin, xmax, nx) # logspace broken in mpld3
    xidx = [i for i, j in a]
    gatex = [xcoor[i] for i in xidx] 
    print "gatex: ", gatex
    ycoor = np.linspace(ymin, ymax, ny)
    yidx = [j for i, j in a]
    gatey = [ycoor[i] for i in yidx]
    print "gatey: ", gatey
    a2 = zip(gatex, gatey) 

    path = Path(a2,b)
    patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
    print "display: patch", len(path), path
    ax[0].add_patch(patch)

    gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=4)
    print "added gatexy: ", gatexy[0].get_data()
    gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    print "added gateline: ", gateline[0].get_data()

#    ax[0].set_ylim(min(gatex)*0.8, max(gatex)*1.1)
#    ax[0].set_xlim(min(gatey)*0.8, max(gatey)*1.1)
    ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
    ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
    plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
    print "linked LinkedDragPlugin"
    
# file markers
    xc = np.zeros(len(names))
    yc = np.zeros(len(names))
    n = (len(names)+1)/2
    for i in range(len(names)):
        xc[i] = 0.1 + 0.5*(i/n)
        yc[i] = 1 + i % n
    print "set xc, yc", xc, yc
    
    points = ax[1].plot(xc, yc, 'ko', markersize=35, alpha=0.0)
    ax[1].scatter(xc, yc, c=np.random.rand(len(names)), s=150, alpha=0.5)
    print "drew file markers", points[0].get_data()

    for i in range(len(names)):
        plt.text(xc[i]+0.02, yc[i], names[i], fontsize=14, 
             verticalalignment='center', bbox=dict(facecolor='red', alpha=0.7))

    print "entered text"
    ax[1].set_xlim(0,1)
    ax[1].set_ylim(0, max(yc)+1)

    linedata = forside.transpose(0, 2, 1).tolist()
    print "linedata>> ", len(linedata), len(linedata[0])
    plugins.connect(fig, LinkedView(points[0], scatpts[0], scatline[0], linedata))

    fig = plt.gcf()
    html = fig_to_html(fig) 
#    return render_template('empty.html', content=html)

    lis = " ".join(channel)
    print "lis>> ", lis
    return render_template('empty1.html', content=html, 
                           xcoor=gatex[:-1], ycoor=gatey[:-1], 
                           channel=lis)
 

@app.route("/replot",methods=['GET','POST'])
def replot():
    if request.method == 'POST':
        print "request form >> ", request.form
        a = request.form.keys()

# read gate x, y coordinates 
        import re
        a = [a[i] for i in range(len(a)) if not re.match(r'[xy]_\d+', a[i]) == None]
        session['selchan'] = request.form['channel']
        print "keys: ", a
        b = [(i.split('_')[0], i.split('_')[1]) for i in a]
        print "split: ", b
        b.sort(key = lambda l: (l[0], int(l[1])))
        print "sorted b: ", b
        c = [x[0]+"_"+x[1] for x in b]
        
        print "ordered keys: ", c
        nxy = len(c)/2
        d = np.reshape(c,(2,-1))
        print "reshaped: ", d, len(d[0])
        x = []; y = []
        for i in d[0]: # xcoor
            print "x coordinates: ", request.form[i], type(request.form[i])
            x.append(float(request.form[i]))
        for i in d[1]: # ycoor
            print "y coordinates: ", request.form[i], type(request.form[i])
            y.append(float(request.form[i]))

        gate = [x, y]        
        print "gate: ", gate
        pid = session['pid']
        chan = request.form['channel']
        sel = db.fcdata.find_one({'_id':ObjectId(pid)})
        sel['gate'] = gate
        db.fcdata.save(sel)

        checkvals = request.form.getlist('fname_check')
        chk = ""
        if not checkvals == None:
            chk = [str(x) for x in checkvals]
            chk = " ".join(chk)
            print "check boxes: ", checkvals, chk
        session['checkbox'] = chk

        return redirect(url_for('redisplay'))       

@app.route("/redisplay", methods=['GET', 'POST'])    
def redisplay():
    pid = session['pid']
    print "pid: ", pid
    sel = db.fcdata.find({'_id':ObjectId(pid)}).next()
    pids = sel['pids'] # ndarray = fdat
    names = sel['filenames']
    channel = sel['channels']
#    print "channel: ", chan
#    histchan = channel.index(chan)
    histchan = int(session['selchan'])
    print "found entry", histchan

# read data
    forside = []
    fdat = []
    for p in pids:
        f = db.fcdata_file.find({'_id': p}).next()
        ndarray = np.array(f['data']) # ndarray = fdat
        fdat.append(ndarray)
        ndat = len(ndarray)
        if ndat < MIN_NDAT:  pass 
        print "found file .. "
    
        x = ndarray[:MAX_NDAT,0]
        y = ndarray[:MAX_NDAT,1]
        xy = np.array(zip(x, y))
        forside.append([x, y])

    forside = np.array(forside)
    print "forside: ", len(forside), len(forside[0]), len(forside[0][0])
    [x, y] = [forside[0][0], forside[0][1]]

# plot forward vs. side        
    fig = plt.figure()
    fig.set_size_inches(8,8)
    gs = gridspec.GridSpec(2,2)
    ax = []
    ax.append(plt.subplot(gs[0,0]))
    ax.append(plt.subplot(gs[0,1]))
    ax.append(plt.subplot(gs[1,:]))

    scatline = ax[0].plot(x, y, 'k', lw=1, alpha=0.)
    scatpts = ax[0].plot(x, y, 'ko', markersize=1)
    #print "lines: ", len(lines), lines
    ax[0].set_title("Forward vs. Side Scatter", fontsize=24)
    
# draw gate
    [gatex, gatey] = sel['gate'] # into two columns
    gatex = gatex + [gatex[0]]
    gatey = gatey + [gatey[0]]    
    gate = zip(gatex, gatey)
    print "gate from db: ", gate
    codes = [Path.MOVETO]
    for i in range(1,len(gate)-1):
        codes.append(Path.LINETO)
    codes.append(Path.CLOSEPOLY)
    print "code from db: ", codes

    path = Path(gate, codes)
    patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
    print "display: patch", len(path), path
    ax[0].add_patch(patch)

    gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=6)
    print "added gatexy: ", gatexy[0].get_data()
    gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    print "added gateline: ", gateline[0].get_data()

#    ax[0].set_ylim(min(gatex)*0.8, max(gatex)*1.1)
#    ax[0].set_xlim(min(gatey)*0.8, max(gatey)*1.1)
    ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
    ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
    plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
    print "linked LinkedDragPlugin"
    
# draw file markers
    xc = np.zeros(len(pids))
    yc = np.zeros(len(pids))
    n = len(pids)
    for i in range(len(pids)):
        xc[i] = 0.2 
        yc[i] = i + 1
    print "set xc, yc", xc, yc

    print "label ", len(names), names[0]    
    points = ax[1].plot(xc[i]+0.3, yc[i], 'ko', markersize=35, alpha=0., label=names[i])
    markers = ax[1].scatter(xc, yc, c=np.linspace(0,1,len(pids)), s=(350 - 200*n/10), alpha=0.3, label=names)
        
    ax[1].set_title("Files", fontsize=24)
#    plugins.connect(fig, PointLabelTooltip(points[0], labels=label)) 
    
#    print "drew file markers", points[0].get_data()

    for i in range(len(names)):
        ax[1].text(xc[i]+0.1, yc[i], names[i], fontsize=(16 - 4*n/10), 
             verticalalignment='center')

    print "entered text"
    ax[1].set_xlim(0,1)
    ax[1].set_ylim(0, max(yc)+0.5)

    linedata = forside.transpose(0, 2, 1).tolist()
    print "linedata>> ", len(linedata), len(linedata[0])
#    plugins.connect(fig, LinkedView(points[0], scatpts[0], scatline[0], linedata))

# draw histogram
    chk = session["checkbox"]
    vert = []
    logbin = np.logspace(0, 4, 50)
    linbin = np.linspace(0, 1000, 50)
    if chk == "":
        logbin = np.logspace(0, 4, 50)
        linbin = np.linspace(0, 1000, 50)
        for i in range(len(pids)):
            ndarray = fdat[i]
            xy = zip(ndarray[:,0], ndarray[:,1])
            print "xy: ", len(xy)
            gated = path.contains_points(xy)
            x = [ndarray[i,histchan] for i in range(len(ndarray[:,2])) if gated[i]]
            print "FL1: ", len(gated), x[:5], len(x)
        #    bins = np.linspace(xmin, xmax, nx)
        #    x = np.random.random(1000)
            h, b = np.histogram(x, linbin)
            h[0] = 0 # anomalous binning?
            b = 10.**(b/1000)
            print "histogram: ", h, np.max(h)
            vert.append(fcs_manhattan(h, b))
    
        print "vert>> ", len(vert), len(vert[0]), len(vert[0][0])  
    # create the line object
        histdata = np.array(vert).tolist()
        v = np.array(vert[0])

        hist = ax[2].plot(v[:,0], v[:,1], '-g', lw=3, alpha=0.5)
        print "histdata: ", len(histdata), len(histdata[0]), len(histdata[0][0])
        plugins.connect(fig, LinkedLinePlugin(markers, hist[0], histdata))
#    plugins.connect(fig, LinkedView2(points[0], hist[0], histdata))
#    plugins.connect(fig, LineLabelTooltip(hist[0]))
    else:   
        session['checkbox'] = ""
        for i in range(len(pids)):
            ndarray = fdat[i]
            xy = zip(ndarray[:,0], ndarray[:,1])
            print "xy: ", len(xy)
            gated = path.contains_points(xy)
            x = [ndarray[i,histchan] for i in range(len(ndarray[:,2])) if gated[i]]
            print "FL1: ", len(gated), x[:5], len(x)
        #    bins = np.linspace(xmin, xmax, nx)
        #    x = np.random.random(1000)
            h, b = np.histogram(x, linbin, normed=True)
            h[0] = 0 # anomalous binning?
            h = h / np.max(h)
            b = 10.**(b/1000)
            print "histogram overlay: ", h, np.max(h)
            vert.append(fcs_manhattan(h, b, smooth=True))
        checkvals = str.split(chk, " ")
        for i in checkvals:
            print "overlaying histograms"
            v = vert[np.int(i)]
            print "v: ", v[:5,:]
            ax[2].plot(v[:,0], v[:,1], lw=1, label=names[np.int(i)])
            hist = ax[2].patches
        ax[2].legend(loc='right')
# plugin to allow click
#            plugins.connect(fig, ClickSelectPlugin(markers, hist[0], histdata))
            
    maxy = -1
    for i in range(len(vert)):
        if max(vert[i][:,1])>maxy: maxy = max(vert[i][:,1])
    ax[2].set_ylim(0, maxy*1.1)
    ax[2].set_xscale('log')
    ax[2].set_title("Histogram", fontsize=24)
    
    print "plugins>>"
    html = fig_to_html(fig)
    print "wrote html>>"

    lis = " ".join(channel)
    print "lis>> ", lis
    
    fnames = "$".join(names)
    print "fnames>> ", fnames
    checkbox = session['checkbox']
    return render_template('empty2.html', content=html, 
                           xcoor=gatex[:-1], ycoor=gatey[:-1], 
                            pid=pid, channel=lis, selchan=histchan,
                            fnames=fnames, chkbox=checkbox)


if __name__ == "__main__":
    app.run(debug=True)
     
