# -*- coding: utf-8 -*-
"""
Name: cyfi.py
This program accepts the typical flow cytometry data in FCS2 (and maybe other formats)
and interactively displays the 1D histogram (and scatter plots in the future) using
browsers. Importantly, the program allows users to interactively define gates in the
forward and side scatter plot, which are then used to display histogram of selected 
cells. The interactive feature is implemented using the mpld3 library. 

The script has been validated using Anaconda-2.2.0 running python 2.7. It generates 
errors in Anaconda2-2.5 and clearly does not run on Anaconda3 (which uses python 3.5).
"""

import os
from flask import Flask, Blueprint, session, render_template, redirect, url_for, request
import numpy as np

from matplotlib import gridspec
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
from mpld3 import plugins, fig_to_html
from mpld3plugins import *

import FlowCytometryTools as fctools
from FlowCytometryTools import FCMeasurement as fcmea
from cyfi_utils import *

from pymongo import MongoClient
from bson import ObjectId

# some initialization
app_cyfi = Flask(__name__)
config = {'UPLOAD_FOLDER' : "c:/Users/sjpark6/IntDev/webapps/cyfiplot/temp"}

"""
The backend is implemented using mongodb. Therefore, mongodb needs to be running 
as a standalone or as a service before this program is launched. The database (flowcy) stores 
flow cy data that is initially uploaded, which is retrieved during each call. The 
data are stored in two collections: 
1. flowcy_series: stores ObjectId of each entry in flowcy_data. Each entry in flowcy_series
correspond to the collection of files that were uploaded at the same time and will be 
analyzed together. Currently, this cannot be updated. 
2. flowcy_data: stores individual flowcy data, i.e. each file. Contains the actual 
flow cy data.
"""

client = MongoClient()
db = client.flowcy
db.flowcy_series.create_index('time', expireAfterSeconds=24*3600)
db.flowcy_data.create_index('time', expireAfterSeconds=24*3600)

MAX_NDAT = 5000
MIN_NDAT = 100

"""
When launched, the program takes to a page which prompts for files info. 
Upon loading the files, the files are read one at a time and stored into the two
collections, flowcy_series and flowcy_data (above), located in the flowcy database.
By default, the forward-v-side scatter plot is displayed. The major peak is automatically
highlighted and indicated using a gate. The gate can be interactively modified.
Once the gate is defined, a histogram of the selected cells can be defined.
"""
@app_cyfi.route('/')
def index():
    return render_template('index.html')
    
@app_cyfi.route("/data_upload", methods=['GET', 'POST'])
def data_upload():
    import datetime
    ctr = 0
    try:
        lis = request.files.getlist('upfile[]')
        names = []; pid_lis = [] # pids for this session
        for f in lis:
            try:
                fname = "f" + str(int(np.random.random()*10**10))     
                fname = config['UPLOAD_FOLDER'] + "/" + fname
                f.save(fname)
                header, flowcy_dat = fctools.parse_fcs(fname, 
                                      meta_data_only=False, 
                                      output_format='ndarray', 
                                      reformat_meta=True)
                s = fcmea(ID='mysample', datafile=fname)
                channel_lis = s.channel_names
                os.remove(fname)
    
                dat = dict()
                dat['filename'] = f.filename
                dat['channel'] = channel_lis
                dat['data'] = flowcy_dat.tolist()
                if len(dat['data']) < MIN_NDAT:
                    raise ValueError('Not enough data here. Skipping')
                
                dat['time'] = datetime.datetime.utcnow()
                result = db.flowcy_data.insert_one(dat)

                names.append(f.filename)
                pid_lis.append(str(result.inserted_id))
                ctr += 1
            except:
                continue

        dat = dict()
        dat['pid_lis'] = pid_lis
        dat['name_lis'] = names
        dat['channel_lis'] = channel_lis
        dat['time'] = datetime.datetime.utcnow()
        result = db.flowcy_series.insert_one(dat)
        series_id = result.inserted_id
        session['series_id'] = str(series_id)
        return redirect(url_for('pre_fvs_plot'))
    except:
        return redirect(url_for('index'))

"""
pre_fvs_plot: the functions with the 'pre' designation is used for rerouting 
purposes. Typically, it obtains the series_id and passes it as a parameter to the
next function, which displays the id as part of the url. This information is used
to retrieve the same session and continue the analysis at a later time up to 24 hr
after the start of the analysis.
"""
@app_cyfi.route('/pre_fvs_plot', methods=['GET', 'POST'])
def pre_fvs_plot():
    try:
        series_id_str = session['series_id']
        if 'gate' in session:
            session.pop('gate')
        return redirect(url_for('fvs_plot', series_id_str=series_id_str))
    except:
        return redirect(url_for('index'))

"""
fvs_plot: forward v. side plot is the first plot that is generated following 
file uploads. All fvs data are available for display, but the first one will 
be displayed by default.
"""
@app_cyfi.route('/fvs_plot/<series_id_str>', methods=['GET', 'POST'])    
def fvs_plot(series_id_str):
    try:
        series_id = ObjectId(series_id_str)
        selected_series = db.flowcy_series.find({'_id' : series_id}).next()
        pid_lis = selected_series['pid_lis']
        names = selected_series['name_lis']
        channel = selected_series['channel_lis']
    
        # read data
        forside = []
        for pid in pid_lis:
            p = ObjectId(pid)
            f = db.flowcy_data.find({'_id': p}).next()
            flowcy_dat = f['data']
            
            ndarray = np.array(flowcy_dat) # ndarray = flowcy_dat
            ndat = len(ndarray)
        
            nmax = min(ndat, MAX_NDAT)
            x = ndarray[:nmax, 0]
            x = np.concatenate((x, np.zeros(MAX_NDAT-nmax)-1))
            y = ndarray[:nmax, 1]
            y = np.concatenate((y, np.zeros(MAX_NDAT-nmax)-1))
            forside.append([x, y])
        
        forside = np.array(forside)
        for i, f in enumerate(forside):
            f.T.tolist()
        [x, y] = [forside[0][0], forside[0][1]]
    
    # plot forward vs. side        
        fig = plt.figure()
        fig.set_size_inches(8,10)
        gs = gridspec.GridSpec(3,1)
        ax = []
        ax.append(plt.subplot(gs[:2,:]))
        ax.append(plt.subplot(gs[2,:]))
    
        scatline = ax[0].plot(x, y, 'k', lw=1, alpha=0.)
        scatpts = ax[0].plot(x, y, 'ko', markersize=1)
        ax[0].set_title("Forward vs. Side Scatter", fontsize=24)
            
        if 'gate' in session:
            [gatex, gatey] = session['gate']             
            gatex = gatex + [gatex[0]]
            gatey = gatey + [gatey[0]]    
            gate = zip(gatex, gatey)
            codes = [Path.MOVETO]
            for i in range(1,len(gate)-1):
                codes.append(Path.LINETO)
            codes.append(Path.CLOSEPOLY)
            path = Path(gate, codes)  
            
#     define and draw initial gate
        else:
            try:
                xtemp = []
                ytemp = []
                for t in forside:
                    tt = t[:, t[0]>0]                    
                    xtemp += tt[0].tolist()
                    ytemp += tt[1].tolist()
                skip = max(len(xtemp)/(5*MAX_NDAT), 1)
#                skip = 1
                x = xtemp[::skip]
                y = ytemp[::skip]                    
                xy = zip(x, y)
                xmax = max(x); xmin = 0
                ymax = max(y); ymin = 0
                xy = np.array([(x0, y0) for x0, y0 in xy if x0<xmax and x0>xmin and y0<ymax and y0>ymin])
                
                nx = 40; dx = float(xmax-xmin)/nx; nx += 1
                ny = 40; dy = float(ymax-ymin)/ny; ny += 1
        
                h2 = np.zeros((nx, ny))
                for i in range(len(xy)):
                    ix = int(xy[i,0]/dx)
                    iy = int(xy[i,1]/dy)
                    try:
                        h2[ix, iy] = h2[ix, iy] + 1
                    except:
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
                    rect = clearRect(h2, incd, rect, thresh) # update the included bins
                    ct = ct + 1
        
                bounds = drawBoundary(incd)
                codes = [Path.MOVETO]
                for i in range(1,len(bounds)-1):
                    codes.append(Path.LINETO)
                codes.append(Path.CLOSEPOLY)
            
                npt = max(len(bounds)/6, 1) # draw a hexagon
                a = bounds[:-1:npt]; a.append(bounds[-1])
                b = codes[:-1:npt]; b.append(codes[-1])
            
                xcoor = np.linspace(xmin, xmax, nx) # logspace broken in mpld3
                xidx = [i for i, j in a]
                gatex = [xcoor[i] for i in xidx] 
                ycoor = np.linspace(ymin, ymax, ny)
                yidx = [j for i, j in a]
                gatey = [ycoor[i] for i in yidx]
                a2 = zip(gatex, gatey) # corresponding to hexagon        
                path = Path(a2,b)
            except:
                gatex = [400, 400, 600, 600, 400]
                gatey = [400, 600, 600, 400, 400]
                path = Path(zip(gatex, gatey), 
                            [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY])

        patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
        ax[0].add_patch(patch)
    
        gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=10)
        gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    
        ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
        ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
        plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
        
#     file markers
        xc = np.zeros(len(names))
        yc = np.zeros(len(names))
        n = (len(names)+1)/2
        for i in range(len(names)):
            xc[i] = 0.1 + 0.5*(i/n)
            yc[i] = 1 + i % n
        
        points = ax[1].plot(xc, yc, 'ko', markersize=35, alpha=0.0)
        ax[1].scatter(xc, yc, c=np.random.rand(len(names)), s=150, alpha=0.5)
    
        for i in range(len(pid_lis)):
            plt.text(xc[i]+0.02, yc[i], names[i], fontsize=14, 
                 verticalalignment='center', bbox=dict(facecolor='red', alpha=0.7))
    
        ax[1].set_xlim(0,1)
        ax[1].set_ylim(0, max(yc)+1)
    
        linedata = []
        for f in forside:
            linedata.append(f.T.tolist())
        plugins.connect(fig, LinkedView(points[0], scatpts[0], scatline[0], linedata))
    
        fig = plt.gcf()
        html = fig_to_html(fig) 
    
        lis = " ".join(channel)
        sid = []; sid.append(series_id_str)
        session['gate'] = [gatex[:-1], gatey[:-1]]
        return render_template('empty1.html', content=html, 
                               xcoor=gatex[:-1], ycoor=gatey[:-1], 
                               channel=lis)
    except:
        return redirect(url_for('index'))

"""
read_gate_info: when an html containing a gate information file submits a POST 
request to plot histogram (or a scatter plot), dissect the tags and exact the 
values for different input names, x_0, x_1, ..., y_0, y_1, ... This may be replaced
in the future if the gate information stored in the database or in the session
object is used.
"""
def read_gate_info(request):
    a = request.form.keys()
    import re
    a = [a[i] for i in range(len(a)) if not re.match(r'[xy]_\d+', a[i]) == None]
    b = [(i.split('_')[0], i.split('_')[1]) for i in a]
    b.sort(key = lambda l: (l[0], int(l[1])))
    c = [x[0]+"_"+x[1] for x in b]
    d = np.reshape(c,(2,-1))
    x = []; y = []
    for i, j in zip(d[0], d[1]): # xcoor
        x.append(float(request.form[i]))
        y.append(float(request.form[j]))
    return [x, y]        

"""
pre_histogram() is used as a target of an html POST request and re-routes the request
to histogram(). pre_histogram() is used to obtain the series_id so that it can be 
attached as part of the url when histogram is displayed. It also obtains the gate
information by dissecting the input values for x_0, x_1, ..., y_0, y_1, ... 
from the POST request. pre_histogram() sets the selected channel, i.e. 'histchan',
to 2, i.e. FL1_H, by default. If 'histchan' is in session, it means histogram() 
has already been called. Therefore, selected channel information is read from the 
html file, empty2.html.
"""
@app_cyfi.route('/pre_histogram',methods=['POST'])
def pre_histogram():
    try:
        series_id_str = session['series_id']
        gate = read_gate_info(request)
        
        session['gate'] = gate
        session['histchan'] = 2
        session['checkbox'] = ''
        return redirect(url_for('histogram', series_id_str=series_id_str))
        
    except:
        return render_template('index.html')

"""
replot_histogram() is used to change the selected histogram channel. FL1_H is the
initial default channel for computing 1D histogram. One can change this on the 
histogram page and replot the histogram for a different channel. The initial 
histogram display page also allows selection of more than one data set for 
overlay. This information is stored in 'checkvals' and passed on to histogram() 
so that the selected files can be displayed together.
"""
@app_cyfi.route('/replot_histogram',methods=['GET','POST'])
def replot_histogram():
    try:
        series_id_str = session['series_id']
        gate = read_gate_info(request)     
        session['gate'] = gate
        
        session['histchan'] = request.form['channel']
        
        checkvals = request.form.getlist('fname_check')
        chk = ''
        if not checkvals == None:
            chk = [str(x) for x in checkvals]
            chk = " ".join(chk)
        session['checkbox'] = chk

        return redirect(url_for('histogram', series_id_str=series_id_str))
    except:
        return redirect(url_for('index'))

"""
histogram() generates 1D histogram. The gate information is retrieved from the
session object, which is updated by either pre_histogram() or replot_histogram().
Both these functions populate the session entry by reading the appropriate variables
from the preceding html files. If session['checkbox'] is defined, then the 
histogram(s) are smoothed. Otherwise, the histogram is drawn as a manhattan plot. 
Because 'checkbox' can be accessed only from the histogram page, the smooth plot
is available only upon re-plotting. Smoothing is done using interp1d() with 'cubic'
splicing.
"""
@app_cyfi.route('/histogram/<series_id_str>',methods=['GET', 'POST'])
def histogram(series_id_str):
    series_id = ObjectId(series_id_str)
    try:
        gate = session['gate']

        selected_series = db.flowcy_series.find({'_id' : series_id}).next()
        pid_lis = selected_series['pid_lis'] # ndarray = fdat
        names = selected_series['name_lis']
        channel_lis = selected_series['channel_lis']
        histchan = int(session['histchan']) 
    
    # retrieve data from db
        forside = []
        fdat = []
        for p in pid_lis:
            p = ObjectId(p)
            f = db.flowcy_data.find({'_id': p}).next()
            ndarray = np.array(f['data']) # ndarray = fdat
            fdat.append(ndarray)
            ndat = len(ndarray)
       
            nmax = min(ndat, MAX_NDAT)
            x = ndarray[:nmax, 0]
            y = ndarray[:nmax, 1]
            forside.append([x, y])

            x = ndarray[:MAX_NDAT,0]
            y = ndarray[:MAX_NDAT,1] 
            xy = np.array(zip(x, y))
            forside.append([x, y])

        forside = np.array(forside)
        [x, y] = [forside[0][0], forside[0][1]]

    # plot forward vs. side        
        fig = plt.figure()
        fig.set_size_inches(10, 10)
        gs = gridspec.GridSpec(2,2)
        ax = []
    #    ax.append(plt.subplot(gs[0,0], xscale='log', yscale='log'))
        ax.append(plt.subplot(gs[0,0]))
        ax.append(plt.subplot(gs[0,1]))
        ax.append(plt.subplot(gs[1,:]))
    
        scatline = ax[0].plot(x, y, 'k', lw=1, alpha=0.) 
        scatpts = ax[0].plot(x, y, 'ko', markersize=1) 
        ax[0].set_title("Forward vs. Side Scatter", fontsize=24)
    #    ax[0].set_xlim([1, 10000])
    #    ax[0].set_ylim([1, 10000])
        
    # draw gate
        [gatex, gatey] = session['gate'] 
        gatex = gatex + [gatex[0]]
        gatey = gatey + [gatey[0]]    
        gate = zip(gatex, gatey)
        codes = [Path.MOVETO]
        for i in range(1,len(gate)-1):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)
    
        path = Path(gate, codes)
        patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
        ax[0].add_patch(patch)
    
        gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=6)
        gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    
        ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
        ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
        plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
        
    # draw file markers
        xc = np.zeros(len(pid_lis))
        yc = np.zeros(len(pid_lis))
        n = len(pid_lis)
        for i in range(len(pid_lis)):
            xc[i] = 0.2 
            yc[i] = i + 1
    
        points = ax[1].plot(xc+0.3, yc, 'ko', markersize=35, alpha=0., label=names[i])
        markers = ax[1].scatter(xc, yc, c=np.linspace(0,1,len(pid_lis)), s=max((350 - 200*n/10), 150), alpha=0.3, label=names)
            
        ax[1].set_title("Files", fontsize=24)
    
        for i in range(len(names)):
            ax[1].text(xc[i]+0.1, yc[i], names[i], fontsize=(16 - 4*n/10), 
                 verticalalignment='center')
        
        ax[1].set_xlim(0,1)
        ax[1].set_ylim(0, max(yc)+0.5)
    # draw histogram
        
        chk = ''
        if 'checkbox' in session:
            chk = session['checkbox']   
        
        vert = []
        logbin = np.logspace(0, 4, 50)
        linbin = np.linspace(0, 1000, 50)
        if chk == '':
            logbin = np.logspace(0, 4, 50)
            linbin = np.linspace(0, 1000, 50)
            for i in range(len(pid_lis)):
                ndarray = fdat[i]
                xy = zip(ndarray[:,0], ndarray[:,1])
                gated = path.contains_points(xy)
                x = [ndarray[i,histchan] for i in range(len(ndarray[:,2])) if gated[i]]
                h, b = np.histogram(x, linbin)
                h[0] = 0 # anomalous binning?
                b = 10.**(4*b/1024)
                vert.append(fcs_manhattan(h, b))
        
        # create the line object
            histdata = np.array(vert).tolist()
            v = np.array(vert[0])
    
            hist = ax[2].plot(v[:,0], v[:,1], '-g', lw=3, alpha=0.5)
            plugins.connect(fig, LinkedLinePlugin(markers, hist[0], histdata))
    
        else:   
            stat = [""] * len(pid_lis)
            for i in range(len(pid_lis)):
                ndarray = fdat[i]
                xy = zip(ndarray[:,0], ndarray[:,1])
                gated = path.contains_points(xy)
                x = [ndarray[j,histchan] for j in range(len(ndarray[:,2])) if gated[j]]
                h, b = np.histogram(x, linbin, normed=True)
                h[0] = 0 # anomalous binning?
                h = h / np.max(h)
                b = 10.**(4*b/1024)
                vert.append(fcs_manhattan(h, b, smooth=True))
                y = 10.**(4*np.array(x)/1024.)
                stat[i] = "Count: {0}".format(len(y)) + "<br>"
                stat[i] += "Median: {0:.1f}".format(np.median(y)) + "<br>"
                stat[i] += "Mean: {0:.1f}".format(np.mean(y))
            checkvals = str.split(chk, " ")
            for i in checkvals:
                v = vert[np.int(i)]
                line, = ax[2].plot(v[:,0], v[:,1], lw=1, label=names[np.int(i)])
#                plugins.connect(fig, plugins.LineHTMLTooltip(line, [stat[np.int(i)]]))
                hist = ax[2].patches
            ax[2].legend(loc='right')

        maxy = -1
        for i in range(len(vert)):
            if max(vert[i][:,1])>maxy: maxy = max(vert[i][:,1])
        ax[2].set_ylim(0, maxy*1.1)
        ax[2].set_xscale('log')
        ax[2].set_title("Histogram for {0}".format(channel_lis[histchan]), fontsize=24)
        
        html = fig_to_html(fig)
        lis = " ".join(channel_lis)
        
        fnames = "$".join(names)
        checkbox = [1, 0, 0]
        if 'checkbox' in session:
            checkbox = session['checkbox']
        session['gate'] = [gatex[:-1], gatey[:-1]]
        return render_template('empty2.html', content=html, 
                               xcoor=gatex[:-1], ycoor=gatey[:-1], 
                                channel=lis, selchan=histchan,
                                fnames=fnames, chkbox=checkbox)
    except:
        return redirect(url_for('index'))

@app_cyfi.route('/pre_scatter', methods=['GET', 'POST'])
def pre_scatter():
    try:
        series_id_str = session['series_id']
        gate = read_gate_info(request)
        session['gate'] = gate
        session['scatchan1'] = 2
        session['scatchan2'] = 3
        session['checkbox'] = ''
        return redirect(url_for('scatter2', series_id_str=series_id_str))       
    except:
        return redirect(url_for('index'))

@app_cyfi.route('/replot_scatter',methods=['GET','POST'])
def replot_scatter():
    try:
        series_id_str = session['series_id']
        gate = read_gate_info(request)                
        session['gate'] = gate
        session['scatchan1'] = request.form['scatchan1']
        session['scatchan2'] = request.form['scatchan2']
        
        return redirect(url_for('scatter2', series_id_str=series_id_str))
    except:
        return redirect(url_for('index'))

"""
scatter: when properly implemented, moving the mouse over different file names
should update the scatter plot. This is similar to fvs plot which is updated 
by moving the mouse over different names. Additionally, the data points will be 
gated using the gate information, similar to how the histogram is generated
using filtered data points. THIS WORK REMAINS TO BE DONE.
"""
@app_cyfi.route('/scatter/<series_id_str>',methods=['GET', 'POST'])
def scatter(series_id_str):
    series_id = ObjectId(series_id_str)
    try:
        gate = session['gate']       
        [gatex, gatey] = session['gate']             
        gatex = gatex + [gatex[0]]
        gatey = gatey + [gatey[0]]    
        gate = zip(gatex, gatey)
        codes = [Path.MOVETO]
        for i in range(1,len(gate)-1):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)
        path = Path(gate, codes)  
        
        selected_series = db.flowcy_series.find({'_id' : series_id}).next()
        pid_lis = selected_series['pid_lis'] 
        names = selected_series['name_lis']
        channel_lis = selected_series['channel_lis']
        scatchan1 = int(session['scatchan1']) 
        scatchan2 = int(session['scatchan2']) 

    # plot forward vs. side        
        fig = plt.figure()
        fig.set_size_inches(10, 10)
        gs = gridspec.GridSpec(3,3)
        ax = []
        ax.append(plt.subplot(gs[0,0]))
        ax.append(plt.subplot(gs[0,1:]))
        ax.append(plt.subplot(gs[1:,:]))
    
    # retrieve data from db
        forside = []
        scatdat = []
        for p in pid_lis:
            p = ObjectId(p)
            f = db.flowcy_data.find({'_id': p}).next()
            ndarray = np.array(f['data']) # ndarray = fdat
            forward  = ndarray[:,0]
            side = ndarray[:,1] 
            forside.append([forward, side])
            gated = path.contains_points(np.array(zip(forward, side)))
            x = [10.**(4.*ndarray[i,scatchan1]/1024) for i in range(len(gated)) if gated[i]]
            x = [np.log10(i) for i in x]
            y = [10.**(4.*ndarray[i,scatchan2]/1024) for i in range(len(ndarray[:,0])) if gated[i]]
            y = [np.log10(i) for i in y]
            scatdat.append([x, y])

        forside = np.array(forside)
        scatdat = np.array(scatdat)

        x = forside[0][0]; x = x[:MAX_NDAT]
        y = forside[0][1]; y = y[:MAX_NDAT]
        ax[0].plot(x, y, 'ko', markersize=1) 
        ax[0].set_title("Forward vs. Side Scatter", fontsize=24)
        
    # draw gate
        [gatex, gatey] = session['gate'] 
        gatex = gatex + [gatex[0]]
        gatey = gatey + [gatey[0]]    
        gate = zip(gatex, gatey)
        codes = [Path.MOVETO]
        for i in range(1,len(gate)-1):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)
    
        path = Path(gate, codes)
        patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
        ax[0].add_patch(patch)
    
        gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=6)
        gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    
        ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
        ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
        plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
        
    # draw file markers
        xc = np.zeros(len(pid_lis))
        yc = np.zeros(len(pid_lis))
        n = len(pid_lis)
        for i in range(len(pid_lis)):
            xc[i] = 0.1
            yc[i] = i + 0.5
    
        points = ax[1].plot(xc, yc, 'ko', markersize=35, alpha=0., label=names[i])
        markers = ax[1].scatter(xc, yc, c=np.linspace(0,1,len(pid_lis)), s=max((350 - 200*n/10), 150), alpha=0.3, label=names)
            
        ax[1].set_title("Files", fontsize=24)
    
        for i in range(len(names)):
            ax[1].text(xc[i]+0.1, yc[i], names[i], fontsize=(16 - 4*n/10), 
                 verticalalignment='center')
        
        ax[1].set_xlim(0,1)
        ax[1].set_ylim(0, max(yc)+0.5)

    # scatter plot
        xmax = -1; ymax = -1;
        for dat in scatdat:
            x = dat[0]; x = x[:MAX_NDAT]
            y = dat[1]; y = y[:MAX_NDAT]
            xmax = max(max(x), xmax)
            ymax = max(max(y), ymax)
        x = scatdat[0][0]; x = x[:MAX_NDAT]
        y = scatdat[0][1]; y = y[:MAX_NDAT]
        scatline = ax[2].plot(x, y, 'k', lw=1, alpha=0.)
        scatpts = ax[2].plot(x, y, 'ko', markersize=1)
#        ax[2].set_xlim(0, xmax)
#        ax[2].set_ylim(0, ymax)
        ax[2].set_xlim(0, 4)
        ax[2].set_ylim(0, 4)
        ax[2].set_title("{0} v. {1}".format(channel_lis[scatchan1], channel_lis[scatchan2]), fontsize=24)
        
        linedata = []
        for f in scatdat:
            fT = np.array(zip(f[0][:MAX_NDAT], f[1][:MAX_NDAT]))
            linedata.append(fT.tolist())
#        linedata = forside.transpose(0, 2, 1).tolist()
        plugins.connect(fig, LinkedView(points[0], scatpts[0], scatline[0], linedata))

        html = fig_to_html(fig)
        lis = " ".join(channel_lis)
        
        fnames = "$".join(names)
        return render_template('empty3.html', content=html, 
                               xcoor=gatex[:-1], ycoor=gatey[:-1], 
                                channel=lis, selchan=2,
                                scatchan1=scatchan1, scatchan2=scatchan2,
                                fnames=fnames)
    except:
        return redirect(url_for('index'))

"""
scatter2() has a different layout. File names on the left. Scatter plot
on the right. On the other hand, scatter (above) has three panels with f-v-s
in the upper left.
"""
@app_cyfi.route('/scatter2/<series_id_str>',methods=['GET', 'POST'])
def scatter2(series_id_str):
    series_id = ObjectId(series_id_str)
    try:
        gate = session['gate']       
        [gatex, gatey] = session['gate']             
        gatex = gatex + [gatex[0]]
        gatey = gatey + [gatey[0]]    
        gate = zip(gatex, gatey)
        codes = [Path.MOVETO]
        for i in range(1,len(gate)-1):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)
        path = Path(gate, codes)  
        
        selected_series = db.flowcy_series.find({'_id' : series_id}).next()
        pid_lis = selected_series['pid_lis'] 
        names = selected_series['name_lis']
        channel_lis = selected_series['channel_lis']
        scatchan1 = int(session['scatchan1']) 
        scatchan2 = int(session['scatchan2']) 

    # plot forward vs. side        
        fig = plt.figure()
        fig.set_size_inches(10, 7)
        gs = gridspec.GridSpec(1,10)
        ax = []
        ax.append(plt.subplot(gs[0,:3]))
        ax.append(plt.subplot(gs[0,3:]))
    
    # retrieve data from db
        forside = []
        scatdat = []
        for p in pid_lis:
            p = ObjectId(p)
            f = db.flowcy_data.find({'_id': p}).next()
            ndarray = np.array(f['data']) # ndarray = fdat
            forward  = ndarray[:,0]
            side = ndarray[:,1] 
            forside.append([forward, side])
            gated = path.contains_points(np.array(zip(forward, side)))
            x = [10.**(4.*ndarray[i,scatchan1]/1024) for i in range(len(gated)) if gated[i]]
            x = [np.log10(i) for i in x]
            y = [10.**(4.*ndarray[i,scatchan2]/1024) for i in range(len(ndarray[:,0])) if gated[i]]
            y = [np.log10(i) for i in y]
            scatdat.append([x, y])

        forside = np.array(forside)
        scatdat = np.array(scatdat)

        x = forside[0][0]; x = x[:MAX_NDAT]
        y = forside[0][1]; y = y[:MAX_NDAT]
#        ax[0].plot(x, y, 'ko', markersize=1) 
#        ax[0].set_title("Forward vs. Side Scatter", fontsize=24)
        
    # draw gate
        [gatex, gatey] = session['gate'] 
        gatex = gatex + [gatex[0]]
        gatey = gatey + [gatey[0]]    
        gate = zip(gatex, gatey)
        codes = [Path.MOVETO]
        for i in range(1,len(gate)-1):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)
    
        path = Path(gate, codes)
        patch = patches.PathPatch(path, facecolor='red', edgecolor='red', lw=2, alpha=0.3)
#        ax[0].add_patch(patch)
    
#        gatexy = ax[0].plot(gatex[:-1], gatey[:-1], 'ro', markersize=6)
#        gateline = ax[0].plot(gatex[:-1], gatey[:-1], 'r', alpha=0) # lines[1]
    
#        ax[0].set_xlim(min(x)*0.8, max(x)*1.1)
#        ax[0].set_ylim(min(y)*0.8, max(y)*1.1)
#        plugins.connect(fig, LinkedDragPlugin(gatexy[0], gateline[0], patch))
        
    # draw file markers
        xc = np.zeros(len(pid_lis))
        yc = np.zeros(len(pid_lis))
        n = len(pid_lis)
        for i in range(len(pid_lis)):
            xc[i] = 0.1
            yc[i] = i + 0.5
    
        points = ax[0].plot(xc, yc, 'ko', markersize=35, alpha=0., label=names[i])
        markers = ax[0].scatter(xc, yc, c=np.linspace(0,1,len(pid_lis)), s=max((350 - 200*n/10), 150), alpha=0.3, label=names)
            
        ax[0].set_title("Files", fontsize=24)
    
        for i in range(len(names)):
            ax[0].text(xc[i]+0.1, yc[i], names[i], fontsize=(16 - 4*n/10), 
                 verticalalignment='center')
        
        ax[0].set_xlim(0,1)
        ax[0].set_ylim(0, max(yc)+0.5)

    # scatter plot
        xmax = -1; ymax = -1;
        for dat in scatdat:
            x = dat[0]; x = x[:MAX_NDAT]
            y = dat[1]; y = y[:MAX_NDAT]
            xmax = max(max(x), xmax)
            ymax = max(max(y), ymax)
        x = scatdat[0][0]; x = x[:MAX_NDAT]
        y = scatdat[0][1]; y = y[:MAX_NDAT]
        scatline = ax[1].plot(x, y, 'k', lw=1, alpha=0.)
        scatpts = ax[1].plot(x, y, 'ko', markersize=1)
        ax[1].set_xlim(0, 4)
        ax[1].set_ylim(0, 4)
        ax[1].set_title("{0} v. {1}".format(channel_lis[scatchan1], channel_lis[scatchan2]), fontsize=24)
        
        linedata = []
        for f in scatdat:
            fT = np.array(zip(f[0][:MAX_NDAT], f[1][:MAX_NDAT]))
            linedata.append(fT.tolist())
#        linedata = forside.transpose(0, 2, 1).tolist()
        plugins.connect(fig, LinkedView(points[0], scatpts[0], scatline[0], linedata))

        html = fig_to_html(fig)
        lis = " ".join(channel_lis)
        
        fnames = "$".join(names)
        return render_template('empty3.html', content=html, 
                               xcoor=gatex[:-1], ycoor=gatey[:-1], 
                                channel=lis, selchan=2,
                                scatchan1=scatchan1, scatchan2=scatchan2,
                                fnames=fnames)
    except:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app_cyfi.secret_key = 'askfsdkfa;skf;asaqk;vzdl'
#    app_cyfi.run(host='0.0.0.0')
    app_cyfi.run(debug='True')
