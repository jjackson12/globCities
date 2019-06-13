import pandas as pd
import copy
import os
import numpy as np
##### This script is to clean and organize data being used for characterization of city scaling properties

### Run Parameters

# List of years to include 
# If multiple years are selected, the values are averaged into the output
# TODO: Is that a good idea?^
years = ['2000','2001','2002','2003','2004','2005']
# filename of data source being cleaned, input
fIn_Data = "GDP_EU.xls"
# filename of data source being added to. Will be deleted. Leave empty if first run
fOut = "EUFeatures.xls"
# filename for output data. This may be created or extended by this script
retFile = "EUFeatures.xls"
# What feature the input dataset contains, e.g. GDP or Patents
feat ="GDP"
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True
# set to True if you are updating with more features (i.e., EUFeatures already has data that should stay there)
updateFeatures = True






# compiles data from outD, a dataframe which already may have several 
# features, with the new data from inD, the cleaned input dataframe
def addData(outD,inD):

    # add new data as new column on the right, empty at first and fill in for loop
    outD[feat] = np.nan
    
    # for every name ALREADY IN THE OUTPUT data 

    for indexI, rowI in inD.iterrows():
        # keep track of whether or not city from new data is already in the old data
        matched = False
        for indexO,rowO in outD.iterrows():
            if cityNameMatch(rowO['METROREG/TIME'],rowI['METROREG/TIME']):
                matched = True
                outD[feat][indexO] = rowI[feat]
                break
        # if the new city is not in the old data, add only if the tag for adding partial data is set to true
        if not matched and addPartialData:
            # Add as new row
            outD = outD.append({'METROREG/TIME' : rowI['METROREG/TIME'], feat : rowI[feat] },ignore_index=True)
    return outD



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


# How to parse the years of data for a given city
def merge(row):
    rowL = list(row)
    for elem in row:
        # The   ':' character means no available data, so we remove it
        if not hasData(elem):
            rowL.remove(elem)
            if(rowL == None):
                return np.nan
    # if there's no available data for that city, return NaN
    if rowL == None or len(rowL) == 0: return np.nan
    # otherwise, return the average after converting to float
    else: 
        rowL = list(map(lambda x: float(x),rowL))
        return np.average(rowL)


def hasData(dat):
    try:
        return isinstance(dat,int) or isinstance(dat,float)
    except AttributeError: 
        if np.isnan(dat) or (":" in dat):
            return False





### Read and Parse input file
dtypes = {'METROREG/TIME': str}
#for year in years:
#    dtypes = dtypes.update({year: float})

# open input file, specifying datatypes and which years to select
inData = pd.read_excel(fIn_Data,dtype=dtypes)    



#merge only selected years of data
inData[feat] = inData[years].apply(merge, axis=1)



# after combining/extracting data, remove other years
inData = inData[['METROREG/TIME',feat]]
# remove cities without data
inData = inData.dropna()
# remove "Non-metropolitan regions in _"
for index,row in inData.iterrows():
    if "Non-metropolitan" in row['METROREG/TIME']:
        inData = inData.drop(index,axis=0)


### add to new file

# if file exists, read it, delete, and rewrite it after adding new data
if updateFeatures and os.path.exists(fOut):
    outData = pd.read_excel(fOut)
    outData = addData(outData,inData)
    os.remove(fOut)
else:
    outData = inData
    if(os.path.exists(fOut)):
        os.remove(fOut)


#set year label for output filename
if len(years) == 1:
    yearLab = years[0]
else:
    yearLab = years[0] + years[-1]

outData.set_index('METROREG/TIME')

outData.to_excel(retFile)