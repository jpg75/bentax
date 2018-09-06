'''
Created on 16/sep/2014

@author: "Gian Paolo Jesi"

'''

from collections import deque
from heuristics import do_heuristic, available_heuristics, risk_response, \
                        tax_payment_response, public_tax_payment_response
from resource import amount, initial_amount, is_alarm, extract, contribute
from aesop import commonstate as cmstate
from aesop.agents.protocol import Protocol
from aesop.agents.core_agents import getProtocolInstances
from aesop.acp import Monitor, factory
import os
import bisect

population_counter = dict()  # current alive population divided by heuristic
public_good_payoff = dict()  # payoff related to the amount of population paying taxes: the more, the better


def weighted_choice_b(weights):
    totals = []
    running_total = 0

    for w in weights:
        running_total += w
        totals.append(running_total)

    rnd = cmstate.r.random() * running_total
    return bisect.bisect_right(totals, rnd)


def add_population(fqn_protocol, *pars , **kpars):
    """Adds a single new node per call.
    
    Represents an oracle which increases the population of each community 
    (heuristic) according to their success (e.g., the bigger the population, 
    the bigger chance to increase).  
    """
    i = cmstate.sim.agentsGraph.number_of_nodes()
    cmstate.sim.agents[i] = factory('aesop.agents.core_agents.NodeAgent', {'name': i})
    cmstate.sim.agents[i].trigger()
    cmstate.sim.agents[i].add_protocol_class(fqn_protocol)
    cmstate.sim.agents[i].protocols['consumer'].my_heuristic = cmstate.r.choice(available_heuristics)
    cmstate.sim.agentsGraph.add_node(i)    
    
            
def count_population(exp_dir='batch_experiments/', protocol_name='consumer', file_name='population.txt'):
    """Count the population relative to a specific protocol.
    Generate a file with: <time> <protocol_name> <size> <alive size> <dead size> 
    """
    global population_counter
    
    pcls = getProtocolInstances('consumer')
    # population_counter.clear()
    population_counter = dict([(k, 0) for k in available_heuristics ])
    
    for p in pcls:
        if p.alive:
            if population_counter.has_key(p.my_heuristic):
                population_counter[p.my_heuristic] += 1
            # else:
            #    population_counter[p.my_heuristic] = 1
                 
    size = len(pcls)
    
    counter = sum(population_counter.values())
    print "Current population of '%s' protocol size is %d; %d alive and %d dead." % ('consumer', size, counter, size - counter)

    # check the folder:
    if not os.path.exists(cmstate.sim.projectDir + exp_dir):
        os.mkdir(cmstate.sim.projectDir + exp_dir)
        
    with open(cmstate.sim.projectDir + exp_dir + file_name , 'a') as f:
        f.write('%d %s %d %d %d\n' % (cmstate.time, protocol_name, size, counter, size - counter))


def set_population_heuristic(greedy=0.5):
    """Set a specific heuristic for each agent. In this case, 50% of agents behave
    according to greedy, while the rest is uniformly distributed over the others.
    """
    pcls = getProtocolInstances('consumer')
    # size = cmstate.sim.agentsGraph.number_of_nodes()
    h_subset = available_heuristics[:]
    h_subset.remove('greedy')
    
    for p in pcls:
        if cmstate.r.random() < greedy:
            p.my_heuristic = 'greedy'
        else:
            p.my_heuristic = cmstate.r.choice(h_subset)


def tax_check(sample=0.05, exp_dir='batch_experiments/', file_name='tpay.txt'):
    """Check a random set of the population if they payed taxes. Agents are no 
    longer killed by the tax check.
    It also generate statistics about the tax payers belonging to each heuristic.
    """
    track_heuristics()

    global population_counter, public_good_payoff
    public_good_payoff.fromkeys(available_heuristics, 0)
    
    pcls = getProtocolInstances('consumer')
    tot_payers = 0
    public_ag_contrib = 0  # public agents contributing
    private_ag_contrib = 0  # private agents contributing
    public_ag = 0  # public agents in the system
    private_ag = 0  # private agents in the system
    public_ext = public_expext = private_ext = private_expext = 0
    payers_per_h = dict([(k, 0) for k in available_heuristics ])
    payers_per_layer_per_h = {'public': dict([(k, 0) for k in available_heuristics ]),
                              'private': dict([(k, 0) for k in available_heuristics ])}
    # avg sadness per h divided for each group: employed, self-employed
    # sadness_per_h = dict([(k, 0.0) for k in available_heuristics ])  # avg sadness per h
    sadness_per_h = {'employed': dict([(k, 0.0) for k in available_heuristics ]),
                     'self-employed': dict([(k, 0.0) for k in available_heuristics ])}
    # res contribution per h and per group: employed, self-employed:
    contribution_per_h = {'employed': dict([(k, 0.0) for k in available_heuristics ]),
                     'self-employed': dict([(k, 0.0) for k in available_heuristics ])}
    # number of (employed, self-employed) per h:
    group_per_h = dict([(k, [0, 0]) for k in available_heuristics ]) 
    
    k = int(len(pcls) * sample) 
    if k < 0: k = 1
    
    # checked sample:
    sample = cmstate.r.sample(pcls, k)
    for item in sample:
        if item.alive and  item.extraction >= 0 and not item.payed:
            # item.how_many_zeros += 4
            item.checked = True
            item.fine += int(item.extraction * 0.3)
            item.checked_at = cmstate.time

    # statistics over all population
    for item in pcls:
        if item.public_sector:
            public_ag += 1
        else: 
            private_ag += 1
        
        if item.alive:
            # sadness_per_h[item.my_heuristic] += item.happyness
            
            # gather data for employed and self-employed groups
            if item.public_sector:
                public_expext += item.exp_extraction
                public_ext += item.extraction
                group_per_h[item.my_heuristic][0] += 1
                sadness_per_h['employed'][item.my_heuristic] += item.happyness
                contribution_per_h['employed'][item.my_heuristic] += item.contribution
                
            else:
                private_expext += item.exp_extraction
                private_ext += item.extraction
                group_per_h[item.my_heuristic][1] += 1
                sadness_per_h['self-employed'][item.my_heuristic] += item.happyness
                contribution_per_h['self-employed'][item.my_heuristic] += item.contribution
                
        if item.alive and item.payed:  # has payed
            tot_payers += 1
            if payers_per_h.get(item.my_heuristic):
                payers_per_h[item.my_heuristic] += 1
                if item.public_sector:
                    public_ag_contrib += 1
                    payers_per_layer_per_h['public'][item.my_heuristic] += 1
                else:
                    private_ag_contrib += 1
                    payers_per_layer_per_h['private'][item.my_heuristic] += 1
            else:  # just in case of error, but should not happen
                payers_per_h[item.my_heuristic] = 1

    # check dividend is not 0!
    private_ext = private_ext / private_ag if private_ag != 0 else 0
    private_expext = private_expext / private_ag if private_expext != 0 else 0
    public_ext = public_ext / public_ag if public_ag != 0 else 0
    public_expext = public_expext / public_ag if public_ag != 0 else 0
    
    # generate the string according to how many heuristics are there
    fstr = ''
    fstr2 = ''
    for h in available_heuristics:  # use available_heuristics to get the same order!
        p_count = population_counter.get(h, 0)
        pph = payers_per_h.get(h, 0)
        sadness_per_h['employed'][h] = sadness_per_h['employed'][h] / p_count if p_count > 0 else 0
        sadness_per_h['self-employed'][h] = sadness_per_h['self-employed'][h] / p_count if p_count > 0 else 0
        
        fstr += ' %d %d' % (p_count, pph)
        
        fstr2 += ' %d %d' % (payers_per_layer_per_h['public'][h], payers_per_layer_per_h['private'][h])
        
        if pph > 0 : 
            # it could be amplified by a heuristic multiplier
            public_good_payoff[h] = pph / p_count if p_count > 0 else 0
        
        
    # check the folder:
    if not os.path.exists(cmstate.sim.projectDir + exp_dir):
        os.mkdir(cmstate.sim.projectDir + exp_dir)
        
    cur_population = sum(population_counter.values())
    with open(cmstate.sim.projectDir + exp_dir + file_name, 'a') as f:
        f.write('%d %d %d%s\n' % (cmstate.time, cur_population, tot_payers, fstr))
    
    with open(cmstate.sim.projectDir + exp_dir + 'layer_tpay.txt', 'a') as f:
        f.write('%d %d %d %d %d %d%s\n' % (cmstate.time, cur_population, public_ag,
                                     private_ag, public_ag_contrib ,
                                     private_ag_contrib, fstr2))
            
    with open(cmstate.sim.projectDir + exp_dir + 'extraction_per_layer.txt' , 'a') as f:
        f.write('%d %d %d %d %d\n' % (cmstate.time, public_expext, public_ext,
                                     private_expext, private_ext))
    
    with open(cmstate.sim.projectDir + exp_dir + 'sadness_per_h.txt', 'a') as f:
        f.write('%d %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f\n' % (cmstate.time,
                                                 sadness_per_h['employed']['random'],
                                                 sadness_per_h['self-employed']['random'],
                                                 sadness_per_h['employed']['imitate_majority'],
                                                 sadness_per_h['self-employed']['imitate_majority'],
                                                 sadness_per_h['employed']['imitate_best'],
                                                 sadness_per_h['self-employed']['imitate_best'],
                                                 sadness_per_h['employed']['greedy'],
                                                 sadness_per_h['self-employed']['greedy'],
                                                 sadness_per_h['employed']['cooperator'],
                                                 sadness_per_h['self-employed']['cooperator']
                                                 ))
    
    with open(cmstate.sim.projectDir + exp_dir + 'groups_per_h.txt', 'a') as f:
        f.write('%d %d %d %d %d %d %d %d %d %d %d\n' % (cmstate.time,
                                                      group_per_h['random'][0], group_per_h['random'][1],
                                                      group_per_h['imitate_majority'][0], group_per_h['imitate_majority'][1],
                                                      group_per_h['imitate_best'][0], group_per_h['imitate_best'][1],
                                                      group_per_h['greedy'][0], group_per_h['greedy'][1],
                                                      group_per_h['cooperator'][0], group_per_h['cooperator'][1]))
    
    with open(cmstate.sim.projectDir + exp_dir + 'contribution_per_h.txt', 'a') as f:
        f.write('%d %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f\n' 
                % (cmstate.time,
                contribution_per_h['employed']['random'],
                contribution_per_h['self-employed']['random'],
                contribution_per_h['employed']['imitate_majority'],
                contribution_per_h['self-employed']['imitate_majority'],
                contribution_per_h['employed']['imitate_best'],
                contribution_per_h['self-employed']['imitate_best'],
                contribution_per_h['employed']['greedy'],
                contribution_per_h['self-employed']['greedy'],
                contribution_per_h['employed']['cooperator'],
                contribution_per_h['self-employed']['cooperator']))


def track_heuristics(exp_dir='batch_experiments/'):
    # check the folder:
    if not os.path.exists(cmstate.sim.projectDir + exp_dir):
        os.mkdir(cmstate.sim.projectDir + exp_dir)

    #available_heuristics = ['random', 'imitate_majority', 'imitate_best',
    #                        'greedy', 'cooperator']

    stat = dict((x, 0) for x in available_heuristics)
    for ag in cmstate.sim.agents.values():
        p = ag.protocols.get('consumer', None)
        if p and p.alive:
            h = p.my_heuristic
            stat[h] += 1

    val = [stat[x] for x in available_heuristics]
    with open(cmstate.sim.projectDir + exp_dir + 'Heuristics' + '.txt', 'a') as f:
        f.write('%d %s\n' % (cmstate.time, ' '.join(map(str, val))))


class Consumer(Protocol):
    
    def __init__(self, *pars, **kpars):
        Protocol.__init__(self, name='consumer', *pars, **kpars)
        self.mortality = True  # default can die
        # print self.immortality
        self.alive = True
        self.e_cost = 0
        self.deltat = 4  # time to wait before taking action
        self.current_deltat = 0
        self.h_history = deque([], self.deltat)
        self.extraction = 0
        self.exp_extraction = 100
        self.my_heuristic = cmstate.r.choice(available_heuristics)
        # if cmstate.r.random() < 0.25:
        #    self.my_heuristic = 'greedy'
            
        a, b = risk_response[self.my_heuristic]
        self.risk_thr = cmstate.r.randrange(a, b, _int=float)
        self.happyness = 0.0  # 0 correspond to max happyness! 
        # the extraction error is an agent feature. It is given by a distro and
        # does not change over time
        self.ext_error = abs(cmstate.r.gauss(0.2, 0.25))
        # agent threshold to change: 90% of the expected extraction
        self.theta = self.exp_extraction * 0.7
        self.how_many_zeros = 0
        
        # Monitors:
        self.addMonitor(Monitor(name='Extraction', xlabel='t', ylabel='y'))
        self.addMonitor(Monitor(name='ExpExtraction', xlabel='t', ylabel='y'))
        self.addMonitor(Monitor(name='Happyness', xlabel='t', ylabel='y'))
        self.addMonitor(Monitor(name='Changes', xlabel='t', ylabel='y'))

    def handleBehavior(self):
        """Active consumer thread.
        """
        
        if not self.alive:
            print "Agent %s dead" % self.host.name
            return
        
        # extract the good according to heuristic
        self.exp_extraction = do_heuristic(self.my_heuristic, self)
        
        # if the agent react to the resource alarm, tries to get 1/3 of what he
        # would like
        if is_alarm() and cmstate.r.uniform(0.0, 1.0) < self.risk_thr:
            self.exp_extraction = int(self.exp_extraction * 0.3)
        
        error = int(self.exp_extraction * self.ext_error)
        if error == 0: error = 1
         
        # print error
        # enforce a cannot be negative!
        a = int(self.exp_extraction - error) if self.exp_extraction - error >= 0 else 1
        b = int(self.exp_extraction + error)
        # print "ranges: %f %f" % (a, b)
        extr_value = abs(cmstate.r.randrange(a , b)) if a != b else b
        self.extraction = extract(extr_value)
        # print "extract: ", self.extraction
        
        # check if it has to die or not:
        if self.extraction == 0 and self.mortality:
            self.how_many_zeros += 1
            if self.how_many_zeros >= 8:
                self.alive = False
                print "Agent %s starved and dies" % self.host.name
        else:
            self.how_many_zeros = 0     
        
        # evaluate own satisfaction
        signal = self.exp_extraction - self.extraction
        if signal < 0:  # means happyness!
            signal = 0
            #  print "WARNING: signal <0: ", signal
        # self.theta = self.exp_extraction + error
        
        self.happyness = signal ** 2 / (signal ** 2 + self.theta ** 2)
        self.h_history.appendleft(self.happyness)
        
        # Monitor mgn:
        self.observe('Extraction', self.extraction)
        self.observe('ExpExtraction', self.exp_extraction)
        self.observe('Happyness', self.happyness)
        
        print "Agent %s extracted %f expecting %f, available: %f" % (self.host.name, self.extraction, self.exp_extraction, amount)
            
        if self.current_deltat < self.deltat:
            self.current_deltat += 1
        else:
            if cmstate.r.uniform(0.0, 1.0) < self._avg_happyness():
            # change heuristic at random:
                h = [x for x in available_heuristics if x != self.my_heuristic ]
                index = cmstate.r.randrange(0, len(h))
                self.my_heuristic = h[index]
                a, b = risk_response[self.my_heuristic]
                self.risk_thr = cmstate.r.randrange(a, b, _int=float)
                
                self.observe('Changes', index)
                print "Agent %s extracted %f expecting %f - changed heuristic to '%s'" % (self.host.name, self.extraction, self.exp_extraction, self.my_heuristic)
            else:
                pass
            
            self.current_deltat = 0  # remember to reset the agent counter
       
        self.theta = (self.exp_extraction * 0.7) if self.exp_extraction != 0 else 1
        # print self.theta     
    
    def process(self, event):
        """Passive consumer Thread.
        """
        if event.payload[0] != 'consumer':
            print "ERROR: wrong dispatch for event: ", event
            return

    def make_message_for(self, neighbor, isReply=False):
        """Packs a MessagEvent and returns it.
        """
        pass

    def _avg_happyness(self):
        """
        Straight average.
        """
        return sum(self.h_history) / max(len(self.h_history), 1) 
    
    
class Consumer2(Consumer):
    def __init__(self, *pars, **kpars):
        Consumer.__init__(self, *pars, **kpars)
        
    def handleBehavior(self):
        """Active consumer thread.
        """
        
        if not self.alive:
            print "Agent %s dead" % self.host.name
            return
        
        # extract the good according to heuristic
        self.exp_extraction = do_heuristic(self.my_heuristic, self)
        
        # if the agent react to the resource alarm, tries to get 1/3 of what he
        # would like
        if is_alarm() and cmstate.r.uniform(0.0, 1.0) < self.risk_thr:
            self.exp_extraction = int(self.exp_extraction * 0.3)
        
        extr_value = self.exp_extraction - ((self.exp_extraction ** 2) / (amount + 1)) 
        if extr_value <= 0:
            extr_value = 1
        
        self.extraction = extract(extr_value)
        # print "extract: ", self.extraction
        
        # check if it has to die or not:
        if self.extraction == 0 and self.mortality:
            self.how_many_zeros += 1
            if self.how_many_zeros >= 8:
                self.alive = False
                print "Agent %s starved and dies" % self.host.name
        else:
            self.how_many_zeros = 0     
        
        # evaluate own satisfaction
        signal = self.exp_extraction - self.extraction
        if signal < 0:  # means happyness!
            signal = 0
            #  print "WARNING: signal <0: ", signal
        # self.theta = self.exp_extraction + error
        
        self.happyness = signal ** 2 / (signal ** 2 + self.theta ** 2)
        self.h_history.appendleft(self.happyness)
        
        # Monitor mgn:
        self.observe('Extraction', self.extraction)
        self.observe('ExpExtraction', self.exp_extraction)
        self.observe('Happyness', self.happyness)
        
        print "Agent %s extracted %f expecting %f, available: %f" % (self.host.name, self.extraction, self.exp_extraction, amount)
            
        if self.current_deltat < self.deltat:
            self.current_deltat += 1
        else:
            if cmstate.r.uniform(0.0, 1.0) < self._avg_happyness():
            # change heuristic at random:
                h = [x for x in available_heuristics if x != self.my_heuristic ]
                index = cmstate.r.randrange(0, len(h))
                self.my_heuristic = h[index]
                a, b = risk_response[self.my_heuristic]
                self.risk_thr = cmstate.r.randrange(a, b, _int=float)
                
                self.observe('Changes', index)
                print "Agent %s extracted %f expecting %f - changed heuristic to '%s'" % (self.host.name, self.extraction, self.exp_extraction, self.my_heuristic)
            else:
                pass
            # reset history:
            # self.h_history[:] = []
            self.current_deltat = 0  # remember to reset the agent counter
       
        self.theta = (self.exp_extraction * 0.7) if self.exp_extraction != 0 else 1
    

class TaxPayer(Consumer):
    TAX = 0.3
    TAX_COEFF = 1.4
    FINE_VALIDITY = 3  # Time for which the fine is applied
    # affects the calculation of the perceived sadness 
    PUBLIC_GOOD_PERCEPTION_COEFF = 0.1
    # Realistic values: 0.3, 0.5, 0.8
    PUBLIC_SECTOR_PROP = 0.8
    PP_DYN = True  # public-private population over time
    PUBLIC_WILLINGNESS_COEFF = 1.3
    PRIVATE_WILLINGNESS_COEFF = 2.0
    
    def __init__(self, *pars, **kpars):
        Consumer.__init__(self, *pars, **kpars)
        self.payed = False  # has payed or not during last cycle
        self.addMonitor(Monitor(name='Taxes', xlabel='t', ylabel='y'))
        
        self.avg_h = 0
        self.checked = False  # True when it has been checked by the authority
        self.checked_at = -1  # time in which has been checked
        self.fine = 0  # fine, calculated by the oracle
        self.contribution = 0.0
        self.public_sector = True if cmstate.r.random() < TaxPayer.PUBLIC_SECTOR_PROP else False

    def handleBehavior(self):
        """Active consumer thread.
        """
        print "TAXPAYER TAX: ", TaxPayer.TAX
        
        if not self.alive:
            print "Agent %s dead" % self.host.name
            return

        self.avg_h = self._avg_happyness()  # precalculate since it is used more than once
        
        # if k turns are passed after being seen not paying
        if self.checked_at > 0 and self.fine > 0:
            if cmstate.time - self.checked_at > TaxPayer.FINE_VALIDITY:
                self.fine = 0  # no more fine to pay
                self.checked_at = -1
        
        # extract the good according to heuristic
        self.exp_extraction = do_heuristic(self.my_heuristic, self)
        
        # if the agent react to the resource alarm, tries to get 1/3 of what he
        # would like
        if is_alarm() and cmstate.r.uniform(0.0, 1.0) < self.risk_thr:
            self.exp_extraction = int(self.exp_extraction * 0.3)
        
        # The eventual fine is subtracted by the actual extraction 
        # The actual extraction value is proportional to the amount of resource
        # available, in the sense that the more the resource the easier to get it
        extr_value = self.exp_extraction - ((self.exp_extraction ** 2) / (amount + 1)) - self.fine
        if extr_value <= 0:
            extr_value = 1
        
        # Apply extract modification according to the willingness to do more, which
        # is specific to self-employed and employed. The chance to apply is 
        # proportional to the current agent happiness (sadness)
        if cmstate.r.random() > self.avg_h:
            if self.public_sector:
                extr_value = extr_value * TaxPayer.PUBLIC_WILLINGNESS_COEFF
            else:
                extr_value = extr_value * TaxPayer.PRIVATE_WILLINGNESS_COEFF
        
        self.extraction = extract(extr_value)
        # print "extract: ", self.extraction
        
        # check if it has to die or not:
        if self.extraction == 0 and self.mortality:
            self.how_many_zeros += 1
            if self.how_many_zeros >= 8:
                self.alive = False
                print "Agent %s starved and dies" % self.host.name
        else:
            self.how_many_zeros = 0     
        
        # evaluate own satisfaction
        signal = max(0, self.exp_extraction - self.extraction)
        #=======================================================================
        # if signal < 0:  # means happiness!
        #     signal = 0
        #=======================================================================
        den = (signal ** 2 + self.theta ** 2) if self.theta != 0 else 1
         
        self.happyness = (signal ** 2 / den) + TaxPayer.PUBLIC_GOOD_PERCEPTION_COEFF * \
            (abs(1 - (sum(public_good_payoff.values()) / len(available_heuristics))))
        
        if self.happyness >= 1:
            self.happyness = 0.99
        
        self.h_history.appendleft(self.happyness)
        
        # Here it pays taxes or not:
        if not self.checked:                
            # if self.extraction > 1 and cmstate.r.uniform(0.0, 1.0) < tax_payment_response[self.my_heuristic]:
            response = 0
            if self.public_sector:
                response = public_tax_payment_response[self.my_heuristic]
            else:
                response = tax_payment_response[self.my_heuristic]
                
            if cmstate.r.uniform(0.0, 1.0) < response:
                if self.extraction <= 1:
                    self.contribution = 1
                else:
                    self.contribution = (self.extraction * TaxPayer.TAX)
                
                self.payed = True
                # if self.contribution > 0:
                contribute(self.contribution * TaxPayer.TAX_COEFF)
            
            else:
                self.payed = False
                self.contribution = 0
        else:  # if it has been checked last cycle never pays!
            self.checked = False
            self.payed = False
            self.contribution = 0
            
        
        # Monitor mgn:
        self.observe('Extraction', self.extraction)
        self.observe('ExpExtraction', self.exp_extraction)
        self.observe('Happyness', self.happyness)
        self.observe('Taxes', self.contribution * TaxPayer.TAX_COEFF)
        
        # print "Agent %s extracted %f expecting %f, available: %f" % (self.host.name, self.extraction, self.exp_extraction, resource.amount)
            
        if self.current_deltat < self.deltat:
            self.current_deltat += 1
        else:
            if cmstate.r.uniform(0.0, 1.0) <= self.avg_h:
            # change heuristic at random:
                h = [x for x in available_heuristics if x != self.my_heuristic ]
                index = cmstate.r.randrange(0, len(h))
                self.my_heuristic = h[index]
                a, b = risk_response[self.my_heuristic]
                # chance to reach to low resource
                self.risk_thr = cmstate.r.randrange(a, b, _int=float)
                
                self.observe('Changes', index)
                print "Agent %s extracted %f expecting %f - changed heuristic to '%s'" % (self.host.name, self.extraction, self.exp_extraction, self.my_heuristic)
            
            
            # change from public sector to private sector or vice-versa
            if TaxPayer.PP_DYN:
                if cmstate.r.uniform(0.0, 1.0) <= self.avg_h:
                    self.public_sector = not self.public_sector                    
                #===============================================================
                # if cmstate.r.uniform(0.0, 1.0) > amount / initial_amount:
                #     self.public_sector = False
                # else: 
                #     self.public_sector = True
                #===============================================================
                
            self.current_deltat = 0  # remember to reset the agent counter
       
        self.theta = (self.exp_extraction * 0.7) if self.exp_extraction != 0 else 1
    
    
