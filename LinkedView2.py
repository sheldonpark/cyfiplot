# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 18:54:48 2014

@author: Sheldon
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import mpld3
from mpld3 import plugins, utils
import fcs_utils

class LinkedView2(plugins.PluginBase):
    """A simple plugin showing how multiple axes can be linked"""

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedView2);
    LinkedView2.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedView2.prototype.constructor = LinkedView2;
    LinkedView2.prototype.requiredProps = ["idpts", "idline", "data"];
    LinkedView2.prototype.defaultProps = {}
    function LinkedView2(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedView2.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;
      console.log(pts)
      console.log(line)
      
      function mouseover(d, i){
        line.data = data[i];
        console.log(line) 
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill);
      }
      pts.elements().on("mouseover", mouseover);

    };
    """

    def __init__(self, points, line, linedata):
#    def __init__(self, points, line, linedata):
        if isinstance(points, matplotlib.lines.Line2D):
            suffix = "pts"
            print "confirmed points"
        else:
            suffix = None
            print "not points"

        self.dict_ = {"type": "linkedview",                      
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}

