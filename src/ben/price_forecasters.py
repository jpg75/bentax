'''
Created on 30/oct/2014

@author: "Gian Paolo Jesi"

'''

from heuristics import do_heuristic
from aesop import commonstate as cmstate
from aesop.agents.protocol import Protocol
from aesop.agents.core_agents import getProtocolInstances
import math
# from aesop.acp import Monitor


r = 0.05
signed_y = 3
pf = 60
# utility measure for each heuristic:
U = {'ADA' : 0.0, 'WRT' : 0.0, 'STR': 0.0, 'LAA' : 0.0}


class MarketPrices(list):
    def __init__(self):
        list.__init__(self)
        self.accumulator = 0
    
    def add(self, x):
        self.append(x)
        self.accumulator += x
        
    def avg(self):
        return self.accumulator / len(self)


class AssetProtocol(Protocol):
    # list of all market prices. TODO:Make a class and make the avg efficient
    prices = MarketPrices()
    # initial prices:
    prices.add(51.36)
    prices.add(52.41)
    
    def __init__(self, *pars, **kpars):
        Protocol.__init__(self, name='assetF', *pars, **kpars)
        # list of expected prices. 2 values required. The rest can be cut 
        self.eprices = []
        self.my_heuristic = cmstate.r.choice(['ADA', 'WRT', 'STR', 'LAA']) 
        self.earnings = 0
        
    def handleBehavior(self):
        """Active consumer thread.
        """
        self.eprices.add(do_heuristic(self.my_heuristic, self))
        # the rest is for the adaptive version:
        pass

    def process(self, event):
        """Passive consumer Thread.
        """
        if event.payload[0] != 'assetF':
            print "ERROR: wrong dispatch for event: ", event
            return
    
        
def new_asset_price():
    """Calculate the asset price at time t using the fmla 4.2 p.43. 
    It is run by the sheet.
    """
    nt = 1 - (6 * math.exp(-200 * abs(AssetProtocol.prices[len(AssetProtocol.prices) - 1] - pf)))  # 6 agents: must be made dynamic
    price = (1 / (1 + r)) * ((1 - nt) * get_avg_forecasts() + (nt * pf) + signed_y + cmstate.r.normalvariate(0.0, 0.5))
    AssetProtocol.prices.add(price)


def get_avg_forecasts():
    pcls = getProtocolInstances('assetF')
    result = 0
    for p in pcls:
        result += pcls.eprice[len(pcls.eprice) - 1]
    
    return result / len(result)


def realize_price():
    """At the end of each cycle each node is informed about its realized price 
    and earnings. It is run by the sheet.
    """
    pcls = getProtocolInstances('assetF')
    result = 0
    for p in pcls:
        e = max(1330 - ((1300 / 49.0) * pow((AssetProtocol.prices[len(AssetProtocol.prices) - 1]) - p.eprices[len(p.eprices) - 1], 2), 0))
        p.earnings += e


def update_heuristc_performance():
    # u = - pow((), 2) +
    pass
