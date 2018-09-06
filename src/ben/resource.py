'''
Created on 16/sep/2014

@author: "Gian Paolo Jesi"


'''
import os
from aesop import commonstate as cmstate
# from heuristics import track_heuristics

policies = ['linear_add', 'double', 'factor']
amount = 100 * cmstate.start_size
resource_limit = amount * 10  # limits the resource growing
initial_amount = amount
current_policy = ''
_alarm = False  # whether or not the resource is in alarm


def reproduce(policy_name, *pars , **kpars):
    """Replenish the resource with some policy. 
    Enforce the respect of the resource limit, since we do not allow infinite resources.
    """
    global amount
    global current_policy
    global _alarm
    # new_amount = amount + linear_add()
    current_policy = policy_name
    new_amount = 0
    track_resource()  # tracking before adding
    # track_heuristics()
    
    if policy_name == 'linear_add':
        #=======================================================================
        # x = linear_add()
        # if amount + x > resource_limit:
        #     new_amount = resource_limit
        # else:
        #     new_amount = amount + x
        #=======================================================================
        new_amount = linear_add()
        
    elif policy_name == 'double':
        x = double(amount)
        if amount + x > resource_limit:
            new_amount = resource_limit
        else:           
            new_amount = amount + x

    elif policy_name == 'flat':
        new_amount = initial_amount
    
    else:
        print "Unknown resource reproduction policy: %s" % policy_name
    
    amount = new_amount 
    if amount >= initial_amount * 0.3:
        _alarm = False


def contribute(k):
    """Tax contribution to the resource.
    """
    global amount
    global _alarm
    amount = amount + k
    # remove the alarm
    if amount >= initial_amount * 0.3:
        _alarm = False
    
    
def extract(k):
    """ Extract the specified amount if available. 
    If the requested amount is not available, 0 is returned no matter the policy.
    In 'double' policy , the resource cannot go beyond 10% its original value.    
    """
    global amount, _alarm
    result = 0
    if current_policy != 'double' and k < amount:
        amount = amount - k 
        result = k
    
    elif current_policy == 'double' and k < amount  and (amount - k > initial_amount * 0.1):
        # print "IN RESOURCE: k : %f, amount %f, amount - k: %f " % (k, amount, amount - k)
        amount = amount - k
        result = k  
    
    # Set the alarm when the resource reaches 30% of its original value:
    if amount < initial_amount * 0.3:
        _alarm = True
               
    return result


def is_alarm():
    """if the resource is in alarm. This triggers a stochastic response by the 
    consumers according to their actual heuristic."""
    return _alarm


def linear_add():
    """Resets to the original amount which is 100 * number of agents in sim.
    """
    # global initial_amount
    # initial_amount = 100 * cmstate.start_size
    return 100 * cmstate.start_size


def double(population):
    return population * 2


def track_resource(exp_dir='batch_experiments/'):
    """Observer method, it is called by the schedule file.
    Tracks the resource amount and writes to file ('Resource.txt'). 
    """
    # check the folder:
    if not os.path.exists(cmstate.sim.projectDir + exp_dir):
        os.mkdir(cmstate.sim.projectDir + exp_dir)
        
    with open(cmstate.sim.projectDir + exp_dir + 'Resource' + '.txt' , 'a') as f:
        f.write('%d %f\n' % (cmstate.time, float(amount)))

    print "current amount: ", amount


