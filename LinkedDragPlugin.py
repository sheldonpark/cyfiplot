# -*- coding: utf-8 -*-
"""
Created on Thu Aug 07 11:19:33 2014

@author: Sheldon
"""
from mpld3 import plugins, utils
import matplotlib as mpl

class LinkedDragPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", LinkedDragPlugin);
    LinkedDragPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedDragPlugin.prototype.constructor = LinkedDragPlugin;
    LinkedDragPlugin.prototype.requiredProps = ["idpts", "idline", "idpatch"];
    LinkedDragPlugin.prototype.defaultProps = {}
    function LinkedDragPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedDragPlugin.prototype.draw = function(){
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
//        console.log(ptsobj)
//        console.log(lineobj)

        var drag = d3.behavior.drag()
            .origin(function(d) { return {x:ptsobj.ax.x(d[0]),
                                          y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);

        lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));
        patchobj.path.attr("d", patchobj.datafunc(ptsobj.offsets,
                                                  patchobj.pathcodes));
        lineobj.data = ptsobj.offsets;
        patchobj.data = ptsobj.offsets;

        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d) {
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
//            console.log(d3.event.x)
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));
          patchobj.path.attr("d", patchobj.datafunc(ptsobj.offsets,
                                                    patchobj.pathcodes));
        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }

        function update() {
          var coor = ptsobj.offsets
//          console.log(coor)
          d3.selectAll('form input.xcoor')
              .data(ptsobj.offsets)
              .attr('name',function(d,i) {return 'x_'+i;})
              .attr('value',function(d) {return d[0];})   
          d3.selectAll('form input.ycoor')
              .data(ptsobj.offsets)
              .attr('name',function(d,i) {return 'y_'+i;})
              .attr('value',function(d){ return d[1]; })   
        }
//        console.log(ptsobj.offsets)
    }

    mpld3.register_plugin("drag", LinkedDragPlugin);
    """

    def __init__(self, points, line, patch):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
            print "confirmed points"
        else:
            suffix = None
            print "not points"

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}

