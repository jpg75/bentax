'''
Created on 17/sep/2014

@author: "Gian Paolo Jesi"


'''
from aesop.examples.ben import resource
from aesop.examples.ben.heuristics import available_heuristics
from  aesop.agents.protocol import Protocol, protocol_graphs
from aesop.agents.core_agents import getProtocolInstances
import aesop.commonstate as cmstate
from Tkinter import BOTH, LEFT 
import matplotlib.pyplot as plt
from aesop.gui.simgui import simGUI
from networkx import Graph, average_clustering, circular_layout, spring_layout, draw_networkx_nodes, draw_networkx_edges, draw_networkx_labels, draw_networkx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class BenGUI(simGUI):
    """Class for visualizing behavioral economics simulation data).
    """
    
    def __init__(self, parent, positions=None):
        super(BenGUI, self).__init__(parent, positions)
        
    def update(self, dynamic_network=False):
        '''Trigger the redraw of all the required GUI elements.
        It is the only interface method and it is called by the underlying 
        simulator.
        When dynamic_network is False, there is no need to regenerate the
        coordinates for positions.
        '''
        if (dynamic_network or self.pos == None):
            keys = range(0, len(cmstate.sim.agentsGraph.nodes()))
            values = [(cmstate.r.randrange(0.0, 1.0, _int=float), cmstate.r.randrange(0.0, 1.0, _int=float)) for x in keys]
            rnd_pos = dict(zip(keys, values))
            self.pos = spring_layout(cmstate.sim.agentsGraph, pos=rnd_pos)
        
        plt.figure(1)
        self.axnet.cla()
        plt.axis('off')
        
        draw_networkx(protocol_graphs['consumer'], pos=self.pos, ax=self.axnet)
        self.graphCanvas.draw()


class ExtendedBenGUI(BenGUI):
    def __init__(self, parent, positions=None):
        super(ExtendedBenGUI, self).__init__(parent, positions)
        # show resource status value:
        self.fig_resource = plt.figure(2, figsize=(5, 6))
        self.ax_resource = self.fig_resource.add_subplot(111)
        
        self.canvas_resource = FigureCanvasTkAgg(self.fig_resource, master=self.lowFrame)
        self.canvas_resource.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        
        # show agent average comsumption over time:
        self.fig_ag_consumption = plt.figure(3, figsize=(5, 6))
        self.ax_ag_consumption = self.fig_ag_consumption.add_subplot(111)
        
        self.canvas_ag_consumption = FigureCanvasTkAgg(self.fig_ag_consumption, master=self.lowFrame)
        self.canvas_ag_consumption.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        
        # show the population for each heuristic:
        self.fig_heuristics = plt.figure(4, figsize=(5, 6))
        self.ax_heuristics = self.fig_heuristics.add_subplot(111)
        
        self.canvas_heuristic = FigureCanvasTkAgg(self.fig_heuristics, master=self.lowFrame)
        self.canvas_heuristic.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        
        self.resource_data = dict()
        self.ag_consumption_data = dict()
        self.heuristic_data = dict()
        
    
    def update(self, dynamic_network=False):
        super(ExtendedBenGUI, self).update(dynamic_network)
        
        self.resource_data[cmstate.time] = resource.amount
        xloc = np.arange(len(available_heuristics))
        bars = np.zeros(len(available_heuristics))
        
        accum = 0
        pl = getProtocolInstances('consumer')
        for p in pl:
            accum += p.extraction
            bars[available_heuristics.index(p.my_heuristic)] += 1
            
        self.ag_consumption_data[cmstate.time] = accum / len(pl)
        
        plt.figure(2)
        self.ax_resource.cla()
        r1 = plt.plot(self.resource_data.keys(), self.resource_data.values(), color='r')
        plt.title('Resource value over time')
        plt.ylabel('Value')
        plt.xlabel('time')
        self.canvas_resource.draw()

        plt.figure(3)
        self.ax_ag_consumption.cla()
        r2 = plt.plot(self.ag_consumption_data.keys(), self.ag_consumption_data.values(), color='g')
        plt.title('Avg. agent resource consumption over time')
        plt.ylabel('Value')
        plt.xlabel('time')
        self.canvas_ag_consumption.draw()
        
        plt.figure(4)
        self.ax_heuristics.cla()
        r3 = plt.bar(xloc + 0.3, bars, width=0.6, color='r', yerr=0)
        plt.xticks(xloc + 0.3, available_heuristics, rotation=10)
        plt.ylim(ymin=0, ymax=50)
        plt.title('Population for each heuristic')
        plt.ylabel('Howmany')
        plt.xlabel('Heuristic')
        self.canvas_heuristic.draw()

        
