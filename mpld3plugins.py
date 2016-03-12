# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 17:51:09 2014

@author: Sheldon
"""

from mpld3 import plugins, utils
import matplotlib as mpl

class EllipsePlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", EllipsePlugin);
    EllipsePlugin.prototype = Object.create(mpld3.Plugin.prototype);
    EllipsePlugin.prototype.constructor = EllipsePlugin;
    EllipsePlugin.prototype.requiredProps = ["idpts", "idline", "idpatch"];
    EllipsePlugin.prototype.defaultProps = {}
    function EllipsePlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    EllipsePlugin.prototype.draw = function(){
        console.log('hello')
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        console.log(ptsobj)
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
        console.log(lineobj)
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        console.log(patchobj)
        
        var mpldiv = d3.select('div')
        console.log(mpldiv)
        
        var mpldsvg = d3.select('svg')
        console.log(mpldsvg)

        var cx = (ptsobj.offsets[0][0] + ptsobj.offsets[1][0])/2
        var rx = (ptsobj.offsets[1][0] - ptsobj.offsets[0][0])/2
        var cy = (ptsobj.offsets[0][1] + ptsobj.offsets[1][1])/2
        var ry = (ptsobj.offsets[1][1] - ptsobj.offsets[0][1])/2
        
        var ellip = [ {'cx': ptsobj.ax.x(cx) + ptsobj.ax.position[0], 
                       'cy': ptsobj.ax.y(cy) + ptsobj.ax.position[1], 
        'rx': Math.abs(ptsobj.ax.x(ptsobj.offsets[1][0]) - ptsobj.ax.x(ptsobj.offsets[0][0]))/2,
        'ry': Math.abs(ptsobj.ax.y(ptsobj.offsets[0][1]) - ptsobj.ax.y(ptsobj.offsets[1][1]))/2 } ]
        console.log(ellip)

        mpldsvg.selectAll('ellipse')
            .data(ellip).enter().append('ellipse')
            .attr('cx', function(d) { return d.cx; })
            .attr('cy', function(d) { return d.cy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })
            .attr('fill', 'none')
            .attr('stroke','black')
            .attr('stroke-width', 1)
            
        var svgellip =  d3.select('svg ellipse')
        console.log(svgellip)
                
        var drag = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj.ax.x(d[0]),
                        y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);
       
        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);
        console.log('hello 4')        

        function dragstarted(d) {
        console.log('hello 5')
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

            var x = ptsobj.offsets
            console.log('hello 3b')
            console.log(x)
            var w = patchobj.data[1][0]
            console.log(w)
            console.log('hello 3c')
            var h = patchobj.data[5][1]
            console.log(h)
            console.log('hello 3d')
            var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                     [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

            patchobj.path.attr("d", patchobj.datafunc(y,
                                                    patchobj.pathcodes));                                                   

            var cx = (ptsobj.offsets[0][0] + ptsobj.offsets[1][0])/2
            var rx = (ptsobj.offsets[1][0] - ptsobj.offsets[0][0])/2
            var cy = (ptsobj.offsets[0][1] + ptsobj.offsets[1][1])/2
            var ry = (ptsobj.offsets[1][1] - ptsobj.offsets[0][1])/2
          
            var a = [ {'cx': ptsobj.ax.x(cx) + ptsobj.ax.position[0], 
                       'cy': ptsobj.ax.y(cy) + ptsobj.ax.position[1], 
                        'rx': Math.abs(ptsobj.ax.x(ptsobj.offsets[1][0]) - ptsobj.ax.x(ptsobj.offsets[0][0]))/2,
                        'ry': Math.abs(ptsobj.ax.y(ptsobj.offsets[0][1]) - ptsobj.ax.y(ptsobj.offsets[1][1]))/2 } ]
            d3.select('svg ellipse')
                .data(a)
            .attr('cx', function(d) { return d.cx; })
            .attr('cy', function(d) { return d.cy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })

        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function update() {
          var coor = ptsobj.offsets
          var x = [coor[0][0], coor[1][0]]
          var y = [coor[0][1], coor[1][1]]
          d3.select('form#analyze').selectAll('input.xcoor')
              .data(x)
              .attr('value',function(d) {return d;})   
          d3.select('form#analyze').selectAll('input.ycoor')
              .data(y)
              .attr('value',function(d){ return d; })   
        }

   } 

    mpld3.register_plugin("drag", EllipsePlugin);
    """
    def __init__(self, points, line, patch):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}

class EllipsePlugin2(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", EllipsePlugin2);
    EllipsePlugin2.prototype = Object.create(mpld3.Plugin.prototype);
    EllipsePlugin2.prototype.constructor = EllipsePlugin2;
    EllipsePlugin2.prototype.requiredProps = ["idpts", "idline", "idpatch",
                                              "idpts2", "idline2", "idpatch2"]
    EllipsePlugin2.prototype.defaultProps = {}
    function EllipsePlugin2(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    EllipsePlugin2.prototype.draw = function(){
        console.log('hello')
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        var ptsobj2 = mpld3.get_element(this.props.idpts2, this.fig);
        console.log(ptsobj)
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
        var lineobj2 = mpld3.get_element(this.props.idline2, this.fig);
        console.log(lineobj)
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        var patchobj2 = mpld3.get_element(this.props.idpatch2, this.fig);
        console.log(patchobj)
        
        var mpldiv = d3.select('div')
        console.log(mpldiv)
        
        var mpldsvg = d3.select('svg')
        console.log(mpldsvg)

        mpldsvg.append('circle').attr('id','circ1')

        var cx = (ptsobj.offsets[0][0] + ptsobj.offsets[1][0])/2
        var rx = (ptsobj.offsets[1][0] - ptsobj.offsets[0][0])/2
        var cy = (ptsobj.offsets[0][1] + ptsobj.offsets[1][1])/2
        var ry = (ptsobj.offsets[1][1] - ptsobj.offsets[0][1])/2
        var cx2 = (ptsobj2.offsets[0][0] + ptsobj2.offsets[1][0])/2
        var rx2 = (ptsobj2.offsets[1][0] - ptsobj2.offsets[0][0])/2
        var cy2 = (ptsobj2.offsets[0][1] + ptsobj2.offsets[1][1])/2
        var ry2 = (ptsobj2.offsets[1][1] - ptsobj2.offsets[0][1])/2
        
        var ellipdat = [ {'cx': ptsobj.ax.x(cx) + ptsobj.ax.position[0], 
                       'cy': ptsobj.ax.y(cy) + ptsobj.ax.position[1], 
        'rx': Math.abs(ptsobj.ax.x(ptsobj.offsets[1][0]) - ptsobj.ax.x(ptsobj.offsets[0][0]))/2,
        'ry': Math.abs(ptsobj.ax.y(ptsobj.offsets[0][1]) - ptsobj.ax.y(ptsobj.offsets[1][1]))/2 }, 
        {'cx': ptsobj2.ax.x(cx2) + ptsobj2.ax.position[0], 
         'cy': ptsobj2.ax.y(cy2) + ptsobj2.ax.position[1], 
         'rx': Math.abs(ptsobj2.ax.x(ptsobj2.offsets[1][0]) - ptsobj2.ax.x(ptsobj2.offsets[0][0]))/2,
         'ry': Math.abs(ptsobj2.ax.y(ptsobj2.offsets[0][1]) - ptsobj2.ax.y(ptsobj2.offsets[1][1]))/2 }
        ]
        console.log(ellip)

        var ellip = mpldsvg.selectAll('ellipse')
            .data(ellipdat).enter().append('ellipse')
            .attr('id', function(d, i) { return 'circ'+(i+1); })
            .attr('cx', function(d) { return d.cx; })
            .attr('cy', function(d) { return d.cy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })
            .attr('fill', 'none')
            .attr('stroke','black')
            .attr('stroke-width', 1)
            
        var svgellip =  d3.select('svg ellipse')
        console.log(svgellip)
                
        var drag = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj.ax.x(d[0]),
                        y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);
        var drag2 = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj2.ax.x(d[0]),
                        y:ptsobj2.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged2)
            .on("dragend", dragended);
       
        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);
        ptsobj2.elements()
           .data(ptsobj2.offsets)
           .style("cursor", "default")
           .call(drag2);
        console.log('hello 4')        

        function dragstarted(d) {
        console.log('hello 5')
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

            var x = ptsobj.offsets
            console.log('hello 3b')
            console.log(x)
            var w = patchobj.data[1][0]
            console.log(w)
            console.log('hello 3c')
            var h = patchobj.data[5][1]
            console.log(h)
            console.log('hello 3d')
            var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                     [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

            patchobj.path.attr("d", patchobj.datafunc(y,
                                                    patchobj.pathcodes));                                                   

            var cx = (ptsobj.offsets[0][0] + ptsobj.offsets[1][0])/2
            var rx = (ptsobj.offsets[1][0] - ptsobj.offsets[0][0])/2
            var cy = (ptsobj.offsets[0][1] + ptsobj.offsets[1][1])/2
            var ry = (ptsobj.offsets[1][1] - ptsobj.offsets[0][1])/2
          
            var a = [ {'cx': ptsobj.ax.x(cx) + ptsobj.ax.position[0], 
                       'cy': ptsobj.ax.y(cy) + ptsobj.ax.position[1], 
                        'rx': Math.abs(ptsobj.ax.x(ptsobj.offsets[1][0]) - ptsobj.ax.x(ptsobj.offsets[0][0]))/2,
                        'ry': Math.abs(ptsobj.ax.y(ptsobj.offsets[0][1]) - ptsobj.ax.y(ptsobj.offsets[1][1]))/2 } ]
            d3.select('svg ellipse#circ1')
                .data(a)
            .attr('cx', function(d) { return d.cx; })
            .attr('cy', function(d) { return d.cy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })

        }
        function dragged2(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj2.ax.x.invert(d3.event.x);
          d[1] = ptsobj2.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj2.path.attr("d", lineobj2.datafunc(ptsobj2.offsets));

            var x = ptsobj2.offsets
            console.log('hello 3b')
            console.log(x)
            var w = patchobj2.data[1][0]
            console.log(w)
            console.log('hello 3c')
            var h = patchobj2.data[5][1]
            console.log(h)
            console.log('hello 3d')
            var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                     [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

            patchobj2.path.attr("d", patchobj2.datafunc(y,
                                                    patchobj2.pathcodes));                                                   

            var cx2 = (ptsobj2.offsets[0][0] + ptsobj2.offsets[1][0])/2
            var rx2 = (ptsobj2.offsets[1][0] - ptsobj2.offsets[0][0])/2
            var cy2 = (ptsobj2.offsets[0][1] + ptsobj2.offsets[1][1])/2
            var ry2 = (ptsobj2.offsets[1][1] - ptsobj2.offsets[0][1])/2
          
            var a = [ {'cx': ptsobj2.ax.x(cx2) + ptsobj2.ax.position[0], 
                       'cy': ptsobj2.ax.y(cy2) + ptsobj2.ax.position[1], 
                        'rx': Math.abs(ptsobj2.ax.x(ptsobj2.offsets[1][0]) - ptsobj2.ax.x(ptsobj2.offsets[0][0]))/2,
                        'ry': Math.abs(ptsobj2.ax.y(ptsobj2.offsets[0][1]) - ptsobj2.ax.y(ptsobj2.offsets[1][1]))/2 } ]
            d3.select('svg ellipse#circ2')
                .data(a)
            .attr('cx', function(d) { return d.cx; })
            .attr('cy', function(d) { return d.cy; })
            .attr('rx', function(d) { return d.rx; })
            .attr('ry', function(d) { return d.ry; })

        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function update() {
          var coor = ptsobj.offsets
          var coor2 = ptsobj2.offsets
          var x = [coor[0][0], coor[1][0], coor2[0][0], coor2[1][0]]
          console.log(x)
          var y = [coor[0][1], coor[1][1], coor2[0][1], coor2[1][1]]
          d3.select('form#analyze').selectAll('input.xcoor')
              .data(x)
              .attr('value',function(d) {return d;})   
          d3.select('form#analyze').selectAll('input.ycoor')
              .data(y)
              .attr('value',function(d){ return d; })   
        }
   } 

    mpld3.register_plugin("drag", EllipsePlugin2);
    """
    def __init__(self, points, line, patch):
        if isinstance(points[0], mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points[0], suffix),
                      "idline": utils.get_id(line[0]),
                      "idpatch": utils.get_id(patch[0]),
                      "idpts2": utils.get_id(points[1], suffix),
                      "idline2": utils.get_id(line[1]),
                      "idpatch2": utils.get_id(patch[1])}

class EmptyPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", EmptyPlugin);
    EmptyPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    EmptyPlugin.prototype.constructor = EmptyPlugin;
    EmptyPlugin.prototype.requiredProps = [];
    EmptyPlugin.prototype.defaultProps = {}
    function EmptyPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    EmptyPlugin.prototype.draw = function(){
    } 

    mpld3.register_plugin("drag", EmptyPlugin);
    """

    def __init__(self):
        self.dict_ = {"type": "drag"}


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
          d3.selectAll('#scatform input.xcoor')
              .data(ptsobj.offsets)
              .attr('name',function(d,i) {return 'x_'+i;})
              .attr('value',function(d) {return d[0];})   
          d3.selectAll('#scatform input.ycoor')
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
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}

class LinkedLinePlugin(plugins.PluginBase):
    """A simple plugin showing how multiple axes can be linked"""

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedLinePlugin);
    LinkedLinePlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedLinePlugin.prototype.constructor = LinkedLinePlugin;
    LinkedLinePlugin.prototype.requiredProps = ["idpts", "idline", "data"];
    LinkedLinePlugin.prototype.defaultProps = {}
    function LinkedLinePlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedLinePlugin.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;
      function mouseover(d, i){
        line.data = data[i];
        console.log(line.data)
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill)
            .style("alpha", 1);
      }
      pts.elements().on("mouseover", mouseover);
    };
    """

    def __init__(self, points, line, linedata):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}

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
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None
        if isinstance(linepts, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",                      
                      "idpts": utils.get_id(points, suffix),
                      "idlinepts": utils.get_id(linepts, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}

#        print self.dict_['idpts'], self.dict_['idlinepts'], self.dict_['idline']

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
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",                      
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}

class VHLinePlugin2(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", VHLinePlugin2);
    VHLinePlugin2.prototype = Object.create(mpld3.Plugin.prototype);
    VHLinePlugin2.prototype.constructor = VHLinePlugin2;
    VHLinePlugin2.prototype.requiredProps = ["idpts", "idline", "idpatch", 
                                                "idpts2", "idline2", "idpatch2"];
    VHLinePlugin2.prototype.defaultProps = {}
    function VHLinePlugin2(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    VHLinePlugin2.prototype.draw = function(){
        console.log('hello')
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        var ptsobj2 = mpld3.get_element(this.props.idpts2, this.fig);
        console.log(ptsobj)
        console.log(ptsobj2)
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
        var lineobj2 = mpld3.get_element(this.props.idline2, this.fig);
        console.log(lineobj)
        console.log(lineobj2)
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        var patchobj2 = mpld3.get_element(this.props.idpatch2, this.fig);
        console.log(patchobj)
        console.log(patchobj2)
        console.log('hello 2')
        
        var drag = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj.ax.x(d[0]),
                        y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);
        var drag2 = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj2.ax.x(d[0]),
                        y:ptsobj2.ax.y(d[1])}; })
            .on("dragstart", dragstarted2)
            .on("drag", dragged2)
            .on("dragend", dragended2);
       
        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);
        ptsobj2.elements()
           .data(ptsobj2.offsets)
           .style("cursor", "default")
           .call(drag2);

        console.log('hello 4')        
        function dragstarted(d) {
        console.log('hello 5')
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }
        function dragstarted2(d) {
        console.log('hello 5')
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

        var x = ptsobj.offsets
        console.log('hello 3b')
        console.log(x)
        var w = patchobj.data[1][0]
        console.log(w)
        console.log('hello 3c')
        var h = patchobj.data[5][1]
        console.log(h)
        console.log('hello 3d')
        var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                 [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

          patchobj.path.attr("d", patchobj.datafunc(y,
                                                    patchobj.pathcodes));                                                   
        }
        function dragged2(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj2.ax.x.invert(d3.event.x);
          d[1] = ptsobj2.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj2.path.attr("d", lineobj2.datafunc(ptsobj2.offsets));

        var x = ptsobj2.offsets
        console.log('hello 3b: foo bar')
        console.log(x)
        var w = patchobj2.data[1][0]
        console.log(w)
        console.log('hello 3c')
        var h = patchobj2.data[5][1]
        console.log(h)
        console.log('hello 3d')
        var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                 [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

          patchobj2.path.attr("d", patchobj2.datafunc(y,
                                                    patchobj2.pathcodes));                                                   
        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function dragended2(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function update() {
          var coor = ptsobj.offsets
          var coor2 = ptsobj2.offsets
          var x = [coor[0][0], coor[1][0], coor2[0][0], coor2[1][0]]
          console.log(x)
          var y = [coor[0][1], coor[1][1], coor2[0][1], coor2[1][1]]
          d3.select('form#analyze').selectAll('input.xcoor')
              .data(x)
              .attr('value',function(d) {return d;})   
          d3.select('form#analyze').selectAll('input.ycoor')
              .data(y)
              .attr('value',function(d){ return d; })   
        }


   } 

    mpld3.register_plugin("drag", VHLinePlugin2);
    """

    def __init__(self, points, line, patch):
        if isinstance(points[0], mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points[0], suffix),
                      "idline": utils.get_id(line[0]),
                      "idpatch": utils.get_id(patch[0]),
                      "idpts2": utils.get_id(points[1], suffix),
                      "idline2": utils.get_id(line[1]),
                      "idpatch2": utils.get_id(patch[1])}

class VHLinePlugin1(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", VHLinePlugin1);
    VHLinePlugin1.prototype = Object.create(mpld3.Plugin.prototype);
    VHLinePlugin1.prototype.constructor = VHLinePlugin1;
    VHLinePlugin1.prototype.requiredProps = ["idpts", "idline", "idpatch"];
    VHLinePlugin1.prototype.defaultProps = {}
    function VHLinePlugin1(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    VHLinePlugin1.prototype.draw = function(){
        console.log('hello')
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        console.log(ptsobj)
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
        console.log(lineobj)
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        console.log(patchobj)
        
        var drag = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj.ax.x(d[0]),
                        y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);
       
        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);
        console.log('hello 4')        

        function dragstarted(d) {
        console.log('hello 5')
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
            console.log(d3.event.x)
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

        var x = ptsobj.offsets
        console.log('hello 3b')
        console.log(x)
        var w = patchobj.data[1][0]
        console.log(w)
        console.log('hello 3c')
        var h = patchobj.data[5][1]
        console.log(h)
        console.log('hello 3d')
        var y = [[0, x[0][1]], [w, x[0][1]], [0, x[1][1]], [w, x[1][1]],
                 [x[0][0], 0], [x[0][0], h], [x[1][0], 0], [x[1][0], h]]

          patchobj.path.attr("d", patchobj.datafunc(y,
                                                    patchobj.pathcodes));                                                   
        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function update() {
          var coor = ptsobj.offsets
          console.log(coor)
          var x = [coor[0][0], coor[1][0]]
          var y = [coor[0][1], coor[1][1]]
          d3.select('form#analyze').selectAll('input.xcoor')
              .data(x)
              .attr('value',function(d) {return d;})   
          d3.select('form#analyze').selectAll('input.ycoor')
              .data(y)
              .attr('value',function(d){ return d; })   
        }

   } 

    mpld3.register_plugin("drag", VHLinePlugin1);
    """

    def __init__(self, points, line, patch):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}

class VLinePlugin1(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", VLinePlugin1);
    VLinePlugin1.prototype = Object.create(mpld3.Plugin.prototype);
    VLinePlugin1.prototype.constructor = VLinePlugin1;
    VLinePlugin1.prototype.requiredProps = ["idpts", "idline", "idpatch"];
    VLinePlugin1.prototype.defaultProps = {}
    function VLinePlugin1(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    VLinePlugin1.prototype.draw = function(){
        console.log('hello')
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        console.log(ptsobj)
        var lineobj = mpld3.get_element(this.props.idline, this.fig);
        console.log(lineobj)
        var patchobj = mpld3.get_element(this.props.idpatch, this.fig);
        console.log(patchobj)
        
        var ystart = ptsobj.offsets[0][1]
        var seqlen = Math.round(ptsobj.offsets[1][0]/0.8)
        var drag = d3.behavior.drag()
            .origin(function(d) { 
                return {x:ptsobj.ax.x(d[0]),
                        y:ptsobj.ax.y(ystart)}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);
       
        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d) {
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        var ytrans = 0
        function dragged(d, i) {
          d[0] = ptsobj.ax.x.invert(d3.event.x);
//          d[1] = ptsobj.ax.y.invert(ystart);
          d[1] = ystart
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x, ptsobj.ax.y(ystart)] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

        var x = ptsobj.offsets
        var x2 = patchobj.data
        var y = [[x[0][0], x2[0][1]], [x[0][0], x2[1][1]], [x[1][0], x2[1][1]], [x[1][0], x2[0][1]]]
          patchobj.path.attr("d", patchobj.datafunc(y,
                                                    patchobj.pathcodes));                                                   
        }

        function dragended(d, i) {
          ytrans = 0
          d3.select(this).classed("dragging", false);          
          update();          
        }
        function update() {
          var coor = ptsobj.offsets
          var x0 = Math.max(coor[0][0], 0), x0 = Math.min(x0, seqlen)
          var x1 = Math.max(coor[1][0], 0), x1 = Math.min(x1, seqlen)
          var x = [x0, x1]
          if (x[1] < x[0]) {
              var t = x[0]
              x[0] = x[1]
              x[1] = t
          }
          var y = [coor[0][1], coor[1][1]]
          d3.select('form#analyze').selectAll('input.xcoor')
              .data(x)
              .attr('value',function(d) {return d;})   
          d3.select('form#analyze').selectAll('input.ycoor')
              .data(y)
              .attr('value',function(d){ return d; })   
          d3.select('input#Start').attr('value',Math.round(x[0]))
          d3.select('input#Finish').attr('value',Math.round(x[1]))   
//          d3.select('form#analyze').selectAll('input#xlim')
//              .data(x)
//              .attr('value', function(d) { return Math.round(d); })
        }

   } 

    mpld3.register_plugin("drag", VLinePlugin1);
    """

    def __init__(self, points, line, patch):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "idpatch": utils.get_id(patch)}


class MousePosition2(plugins.MousePosition):
    JAVASCRIPT = r"""
    
    """
