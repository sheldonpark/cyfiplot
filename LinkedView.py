# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 18:54:48 2014

@author: Sheldon
"""

import matplotlib
from mpld3 import plugins, utils

class LinkedView(plugins.PluginBase):
    """A simple plugin showing how multiple axes can be linked"""

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedViewPlugin);
    LinkedViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedViewPlugin.prototype.constructor = LinkedViewPlugin;
    LinkedViewPlugin.prototype.requiredProps = ["idpts", "idlinepts", "idline", "data"];
//    LinkedViewPlugin.prototype.requiredProps = ["idpts", "idline", "data"];
    LinkedViewPlugin.prototype.defaultProps = {}
    function LinkedViewPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedViewPlugin.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var linepts = mpld3.get_element(this.props.idlinepts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;
      console.log(pts)
      console.log(linepts)
      console.log(line)
      
      linepts.elements()
         .data(linepts.offsets)
         .style("cursor", "default")
         
       
      function mouseover(d, i){
        line.data = data[i];
        linepts.offsets = line.data
        console.log(linepts)
        console.log(line)
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill);
        console.log(line.datafunc(line.data));

        var x = line.datafunc(line.data);
//        console.log(x);
        var y = x.replace(/L/g," ").replace("M","").split(" ");
        console.log(y);
        var z = []
        for (i=0; i<y.length; i++) {
            z[i] = y[i].split(",");
        }
//        console.log(z);        
        linepts.elements()
            .attr("transform", function(d, i) {
                return "translate(" + parseFloat(z[i][0]) 
                                + "," + parseFloat(z[i][1]) + ")";});        
      }
      pts.elements().on("mouseover", mouseover);

    };
    """

    def __init__(self, points, linepts, line, linedata):
#    def __init__(self, points, line, linedata):
        if isinstance(points, matplotlib.lines.Line2D):
            suffix = "pts"
            print "confirmed points"
        else:
            suffix = None
            print "not points"
        if isinstance(linepts, matplotlib.lines.Line2D):
            suffix = "pts"
            print "confirmed points"
        else:
            suffix = None
            print "not points"

        self.dict_ = {"type": "linkedview",                      
                      "idpts": utils.get_id(points, suffix),
                      "idlinepts": utils.get_id(linepts, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}

#        print self.dict_['idpts'], self.dict_['idlinepts'], self.dict_['idline']

