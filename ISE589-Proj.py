# -*- coding: utf-8 -*-
"""
Created on Sun Dec  2 14:06:13 2018

@author: Bpi
"""
#Assumptions
# 155 machines works constantly 8 hours/day 5 days/wk and 50 wks/yr.
#Each machine fails randomly between 800-1000 hours. Immediately replace with spares.
#Repairers fixes the failed machine. It take rabdomly 4-10 hrs. 
#After fixes, it returns to the spares.
# Repairer cost $60/hr; Spare cost $3000/day; 
#If spare is not available, opportunity cost $1,000/hr/machine

# Daily operating cost = spare machine + repairers

import simpy        #importing required packages.
import numpy as np
import os

import csv
import io
#mn = 0
def machine_number():    
    mn = 0
    path = os.getcwd()
    with io.open(path+"/Masked_data.csv") as f:
        reader = csv.DictReader(f)
        mn = int(sum([bool(row["Material Desc"]) for row in reader]))
        return mn

#m = machine_number(mn)

def factory_run(env, repairers, spares):  #cost calculation
    global cost                           # same cost thru program
    
    cost = 0.0
    value = machine_number()
    
    for i in range(value):                     # no of machines
        env.process(operate_machine(env, repairers, spares))
        
    while True:                     #it will update the cost each time for 8 hrs
        cost += 60*8*repairers.capacity +3000*spares.capacity
        yield env.timeout(8.0)

def operate_machine(env, repairers, spares):   #waiting for machine to break and fix it
    global cost
    
    while True:                         
        yield env.timeout(generate_time_to_failure())
        t_broken = env.now
        print ("{:.3f} machine broke".format(t_broken))
        env.process(repair_machine(env, repairers, spares))
        
        yield spares.get(1)     #get a spare and launch repair process
        t_replaced = env.now    #log what time it is broken
        print ("{:.3f} machine replaced".format(t_replaced))
        cost += 1000*(t_replaced-t_broken)

   
def repair_machine(env, repairers, spares):   #repair process
    with repairers.request() as request:
        yield request
        yield env.timeout(generate_repair_time())
        yield spares.put(1)                     #after repair, putting back in spare pool
    print ('{:.3f} repair complete'.format(env.now))
    
    
def generate_time_to_failure():              #define time to failure
    return np.random.uniform(800, 1000)

def generate_repair_time():         #define repair time
    return np.random.uniform(4,10)

obs_time = []
obs_cost = []
obs_spares = []

def observe(env, spares):
    while True:
        obs_time.append(env.now)
        obs_cost.append(cost)
        obs_spares.append(spares.level)
        yield env.timeout(1.0)
        
np.random.seed(0)
env = simpy.Environment()

repairers = simpy.Resource(env, capacity=3)   #3 repairers in staff
spares = simpy.Container(env, init=20, capacity=50) #initially 20 spares and total capacity is 50 spares

env.process(factory_run(env, repairers, spares)) #factory environment
env.process(observe(env, spares))

env.run(until=8*5*50)     #environment time
            
import matplotlib.pyplot as plt
            
plt.figure()
plt.step(obs_time, obs_spares, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('Spares Level')
            
plt.figure()
plt.step(obs_time, obs_cost, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('Cost Incurred')
plt.savefig('image.pdf')
print ('total cost was {:.3f}'.format(obs_cost[-1]))
            