import pandas as pd
import copy
import os
import numpy as np
##### This script is to clean and organize data being used for characterization of city scaling properties

### Run Parameters

# TODO: Get data again, don't delete country indicators, and separate into different countries in different sheets(?)

# List of years to include 
# If multiple years are selected, the values are averaged into the output
# TODO: Is that a good idea?^
years = ['2000','2001','2002','2003','2004','2005']
# filenames of data source being cleaned, input
# TODO: Reformat with adding cities as index, try to avoid weird outputs
fIn_Data = {"GDP": "GDP_EU.xls","Population":"PopEU.xls","Patents":"PatentEU.xls"}
# spreadsheet connecting countries with cities
# filename of data source being output. Will be deleted if already existing.
fOut = "EUFeatures.xls"
# What feature the input dataset contains, e.g. GDP or Patents
feats = ["Population","GDP","Patents"]
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True
# list of countries to include
# full:
allCountries = ["United Kingdom","Brussels","Germany","France","Czech Republic","Switzerland","Spain","Portugal"]

includeCountries = allCountries
#TODO: Fix this change elsewhere; update allCountries list

# compiles data from outD, a dataframe which already may have several 
# features, with the new data from inD, the cleaned input dataframe
def addData(outD,inD):

    if outD.empty:
        return inD

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

def splitCountries(rawData):
    countryTables = {}
    currCountry = 'START'
    for index, row in rawData.iterrows():
        cityName = row['METROREG/TIME']
        if cityName in allCountries:
            if not 'START' in currCountry:
                #select from previous countryName to next country name (then subtract the country data)
                countryTables[currCountry] = rawData.loc[currCountry:cityName][1:-1]
            currCountry = cityName
    return countryTables



### Read and Parse input file
dtypes = {'METROREG/TIME': str}
#for year in years:
#    dtypes = dtypes.update({year: float})



outData = {}

for feat in feats:
    # open input file, specifying datatypes and which years to select
    inDataRaw = pd.read_excel(fIn_Data[feat],dtype=dtypes)    

    # split raw input into countries
    # inData: map: country name -> dataframe
    inData = splitCountries(inDataRaw)

    for country in includeCountries:
        # Check if country is in data
        if not country in inData:
            exceptionMsg = country + " not found! input data includes countries "+
            "(note there may be others not caught if they were not included in allCountries parameter): "+inData.keys()
            raise Exception(exceptionMsg)

        #merge only selected years of data
        inData[country][feat] = inData[country][years].apply(merge, axis=1)

        # after combining/extracting data, remove other years
        inData[country] = inData[country][['METROREG/TIME',feat]]
        # remove cities without data
        inData[country] = inData[country].dropna()
        # remove "Non-metropolitan regions in _"
        for index,row in inData[country].iterrows():
            if "Non-metropolitan" in row['METROREG/TIME']:
                inData[country] = inData[country].drop(index,axis=0)

        # if outData is empty
        if not bool(outData) or not country in outData:
                outData[country] = inData[country]
        else:
            outData[country] = addData(outData[country],inData[country])


    ### add to new file

# if file exists, delete it, and rewrite it after adding new data
if os.path.exists(fOut):
    os.remove(fOut)

# write each country data to different sheets in output
with pd.ExcelWriter(fOut) as writer:
    for country in includeCountries:
        outData[country].set_index('METROREG/TIME')
        outData[country].to_excel(writer, sheet_name=country)
