import pandas as pd
import os
import numpy as np
##### This script is to clean and organize data being used for characterization of city scaling properties

### Run Parameters

# List of years to include 
# If multiple years are selected, the values are averaged into the output
# TODO: Is that a good idea?^
years = [2000]
# filename of data source being cleaned, input
fIn_Data = "PopEU.xls"
# filename of data source being cleaned, being written to. Leave empty if first run
fOut = ""
# What feature the input dataset contains, e.g. GDP or Patents
feat ="GDP"
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True




### Read and Parse input file

# open input file, specifying datatypes and which years to select
inData = pd.read_excel(fIn_Data,names=years.insert(0,'METROREG/TIME'),dtype={'METROREG/TIME': str})    



# How to parse the years of data for a given city
def merge(row):
    for elem in row:
        # The   ':' character means no available data, so we remove it
        if ':' in elem:
            row = row.remove(elem)
    # if there's no available data for that city, return NaN
    if row.empty(): return np.Nan
    # otherwise, return the average
    else: return np.average(row)

inData[feat] = inData.apply(merge, axis=1)

# after combining/extracting data, remove other years
inData = inData['METROREG/TIME',feat]
# remove cities without data
inData[feat] = inData[feat].dropna()


    

# if file exists, read it, delete, and rewrite it after adding new data
if os.path.exists(fOut):
    outData = pd.read_excel(fOut)
    outData = addData(outData,inData)
    os.remove(fOut)
else:
    outData = inData


#set year label for output filename
if len(years) == 1:
    yearLab = years[0]
else:
    yearLab = years[0] + years[-1]
# filename for output data. This may be created or extended by this script
retFile = "clean_"+feat+"_"+yearLab+".xls"

outData.to_excel(retFile)








# compiles data from outD, a dataframe which already may have several 
# features, with the new data from inD, the cleaned input dataframe
def addData(outD,inD):
    # column of input feature data ordered by the city list of the output file
    featCol = []
    # indexes selected to add
    selected = []

    # for every name ALREADY IN THE OUTPUT data 
    for cityOut in outD['METROREG/TIME']:
        for index, row in inD.iterrows():
            if cityNameMatch(cityOut,row['METROREG/TIME']):
                featCol = featCol.append(row[feat])
                selected = selected.append(index)
    # add new data as new column on the right
    outD[feat] = featCol
    # add data for cities not already included in the output dataset
    if(addPartialData):
        for index, row in inD.iterrows():
            if index not in selected:
                # Add as new row
                outD = outD.append({'METROREG/TIME' : row['METROREG/TIME'], feat : row[feat] },ignore_index=True)


# determine if two cities, with names potentially spelled differently and/or 
# in different languages, are the same cities. Cities with more than one way 
# of spelling will have them separated by '/'
def cityNameMatch(name1,name2):
    name1List = name1.split('/')
    name2List = name2.split('/')
    for subName1 in name1List:
        for subName2 in name2List:
            if (subName1 in subName2) or (subName2 in subName1):
                return True
    return False