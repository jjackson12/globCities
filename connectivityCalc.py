import pandas as pd
import copy
import os
import numpy as np

### This script is used to convert global firm presence metrics into city-based connectivity parameters

# name of input file with service values
fIn = "Data/da11.xls"
# name of output file with connectivity parameters
fOut = "Data/Connectivities_SYM.xls"
# connectivity Measure: Either 'symmetric' or 'asymmetric'
connectivityMetric = "symmetric"


# read in data. These represent the service values v_ij (See Yang 2013)
v = pd.read_excel(fIn,dtypes = {"Cities":str})
# set index
v = v.set_index("Cities")
# number of cities in data
cities = list(v.index)
cityLen = len(cities)

#given ... 
def calcASYM(vja,vjb):
    if vja == 0 and vjb == 0:
        return 0
    else:
        return 2*vja/(vja+vjb)



# This is the city dyad-connectivity matrix, with rows and columns both city names, with
#   the matrix values as mutual connectivitys
cdc = pd.DataFrame(np.zeros((cityLen,cityLen)), index=cities, columns=cities,dtype=float)

i=0
# calculate cdc matrix
print("Calculting cdc matrix...")
for a in cities:
    i =i+1
    if i%10==0:
        print("completed cities: "+str(i)+"/"+str(cityLen))
    for b in cities:
        # leave v_ii entries equal to zero so they do not contribute to sum
        if not a==b:
            if connectivityMetric=="symmetric":
                cdc[b][a] = np.sum(v.loc[a]*v.loc[b])
            elif connectivityMetric=="asymmetric":
                cdc[b][a] = np.sum(list(map(calcASYM, v.loc[a], v.loc[b])))
        

# this is the global network connectivity list. Each city gets one value
gnc = pd.DataFrame(np.zeros((cityLen,2)), index=cities, columns=["Connectivity","Connectivity (normalized)"])

# calculate gncs as sum of each city's connectivity with every other city is connected with
for city in cities:
    gnc["Connectivity"][city] = np.sum(cdc.loc[city])



# normalize to 1 for percent Total connectivity
maxConnectivity = np.max(gnc["Connectivity"])
for city in cities:
    gnc["Connectivity (normalized)"][city] = gnc["Connectivity"][city]/maxConnectivity

# save to excel
gnc.to_excel(fOut)
