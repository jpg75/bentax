'''
Created on 16/sep/2014

@author: "Gian Paolo Jesi"

'''

# vedere per i pensionati

import resource
from aesop import commonstate as cmstate
from aesop.agents.core_agents import getProtocolInstances
import networkx as nx
import os

available_heuristics = ['random', 'imitate_majority', 'imitate_best',
                     'greedy', 'cooperator']

# bad greedy: (0, 0.2), good greedy: (0.8, 0.99)
response_values = [(0.0, 1.0), (0.6, 0.8), (0.4, 0.6), (0.8, 0.99), (0.8, 1.0)]
tax_payment_values = [0.5, 0.6, 0.7, 0.1, 0.99]
public_sector_payment_values = [0.8, 0.85, 0.9, 0.6, 0.99]

#public_sector_payment_values = [0.9, 0.9, 0.9, 0.9, 0.99]  # extreme version

# ranges of sensitivity to risk for each heuristic  
risk_response = dict(zip(available_heuristics, response_values))
# probability of paying tax per heuristic
tax_payment_response = dict(zip(available_heuristics, tax_payment_values))
public_tax_payment_response = dict(zip(available_heuristics, tax_payment_values))


def do_heuristic(h_name, protocol_obj):
    """Entry point of the module. The name of the heuristic is provided and must 
    be listed into available_heuritics. 
    """
    if (h_name == 'random'):
        return random_heuristic(protocol_obj)
    elif h_name == 'imitate_majority':
        return imitate_majority_heuristic(protocol_obj)
    elif h_name == 'imitate_best':
        return imitate_best_heuristic(protocol_obj)
    elif h_name == 'search_best':
        return search_best_heuristic(protocol_obj)
    elif h_name == 'imitate_majority_green':
        return imitate_majority_green_heuristic(protocol_obj)
    elif h_name == 'greedy':
        return greedy_heuristic(protocol_obj)
    elif h_name == 'cooperator':
        return cooperator_heuristic(protocol_obj)
    else:
        print "Unknown heuristic: %s" % h_name
        return None


def random_heuristic(protocol_obj):
    """Decides at random how much resource to consume. By default it takes a 
    random between 0 and the twice total amount initially available divided by the actual 
    node population. The idea is to keep the consumption at the sustainable 
    limit.
    """
    size = nx.number_of_nodes(cmstate.sim.agentsGraph)
    upper = (resource.initial_amount / size) * 2
    # print "upper ", upper
    result = cmstate.r.randint(0, upper)
    # print result  
    return abs(result)

    
def imitate_majority_heuristic(protocol_obj):
    """It is actually an average policy, since we expect a lot of variance in 
    the extraction amount.
    """
    # size = nx.number_of_nodes(cmstate.sim.agentsGraph)
    pcls = getProtocolInstances('consumer')
    accum = 0
    size = 0
    for p in pcls:
        if p.alive:
            accum += p.exp_extraction
            size += 1
    result = accum / size
    # print "imit majority: ", result
    return abs(result)


def imitate_best_heuristic(protocol_obj):
    """Get the same extraction value as the 1st agent it founds having a better
    happyness value.
    """
    pcls = getProtocolInstances('consumer')
    result = protocol_obj.extraction
    for p in pcls:
        if p.alive and p != protocol_obj:
            # must be > since 'happyness' means 'sadness'!
            if p.happyness < protocol_obj.happyness:
                result = p.extraction
                break
            
    # return imitate_majority_heuristic(protocol_obj)
    return abs(result)


def search_best_heuristic(protocol_obj):
    """Get the same extraction value as the best agent in the network.
    """
    pcls = getProtocolInstances('consumer')
    result = protocol_obj.extraction
    mid = 5
    for p in pcls:
        if p.alive and p != protocol_obj:
            # must be > since 'happyness' means 'sadness'!
            if p.happyness < mid:
                mid = p.happyness
                result = p.extraction
                            
    # return imitate_majority_heuristic(protocol_name)
    return abs(result)


def imitate_majority_green_heuristic(protocol_obj):
    """Imitate the majority , but it takes a 10% less extraction value in order
    to be 'green'. 
    """
    result = imitate_majority_heuristic(protocol_obj) 
    return abs(int(result * 0.9))
    
    
def greedy_heuristic(protocol_obj):
    """A greedy agent tries to get more from the resource at every step if 
    the previous attempt went fine (e.g., happyness=0). At each step it tries to 
    extract 15% more; instead, it retries to extract the same amount if the 
    previous attempt went wrong.
    """
    if protocol_obj.happyness == 0:
        return protocol_obj.exp_extraction * 1.15  # 15% increase
    else: 
        return protocol_obj.exp_extraction
    
    
def cooperator_heuristic(protocol_obj):
    """According to the previous result (happyness = expected - extraction) the agent
    increase or decrease the amount to get by a constant fixed amount (+/-15%).
    """
    if protocol_obj.happyness >= 0 and protocol_obj.happyness <= 0.15:
        return protocol_obj.exp_extraction * 1.15  # 15% increase
    else:
        return protocol_obj.exp_extraction * 0.85  # -15% instead 
     
