import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import mpld3
from mpld3 import plugins, utils
import fcs_utils

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
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill)
            .style("alpha", 1);
      }
      pts.elements().on("mouseover", mouseover);
    };
    """

    def __init__(self, points, line, linedata):
        if isinstance(points, matplotlib.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}
