import pandas as pd
import copy
import os
import numpy as np
##### This script is to clean and organize data being used for characterization of city scaling properties

### Run Parameters

# If multiple years are selected, the values are averaged into the output
# TODO: Is that a good idea?^
years = ['2000','2001','2002','2003','2004','2005']
# filenames of data source being cleaned, input
fIn_Data = {"GDP": "GDP_EU.xls","Population":"PopEU.xls","Patents":"PatentEU.xls","gini":"gini_2016UK.xls","Connectivity":"da12.xls"}
# spreadsheet connecting countries with cities
fIn_CountryCities = "CountryCities.xlsx"
# filename of data source being output. Will be deleted if already existing.
fOut = "EUFeatures.xls"
# What feature the input dataset contains, e.g. GDP or Patents
feats = ["Population","GDP","Patents","gini","Connectivity"]
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True
# list of countries to include. Either write "ALL" or give a list
includeCountries = ['ALL']
# cities to exclude due to aggregation into collective MAs.
# TODO: Consider combining these data into the one collective MA
excludeCities = ['Blackburn','Blackpool','Preston']

# compiles data from outD, a dataframe which already may have several 
# features, with the new data from inD, the cleaned input dataframe
def addData(outD,inD):

    if outD.empty:
        return inD

    # add new data as new column on the right, empty at first and fill in for loop
    outD[feat] = np.nan
    
    # for every name ALREADY IN THE OUTPUT data 

    for cityI, rowI in inD.iterrows():
        # keep track of whether or not city from new data is already in the old data
        matched = False
        for cityO,rowO in outD.iterrows():
            if cityNameMatch(cityO,cityI):
                matched = True
                outD[feat][cityO] = rowI[feat]
                break
        # if the new city is not in the old data, add only if the tag for adding partial data is set to true
        if not matched and addPartialData:
            # Add as new row
            outD = outD.append(rowI)
    return outD



# determine if two cities, with names potentially spelled differently and/or 
# in different languages, are the same cities. Cities with more than one way 
# of spelling will have them separated by '/'
def cityNameMatch(name1,name2):
    
    name1List = name1.lower().replace("(nuts 2010)","").split('/')
    name2List = name2.lower().replace("(nuts 2010)","").split('/')
    for subName1 in name1List:
        for subName2 in name2List:
            #if (subName1 in subName2 or subName2 in subName1) and not subName1.strip() == subName2.strip():
            #    print("edge case matching - %s , %s", (subName1, subName2))
            # TODO: Matching false positives (Kiel & Kielce)
            #if (subName1 in subName2) or (subName2 in subName1):
            if subName1.strip() == subName2.strip():
                return True
    return False
#print(cityNameMatch())

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
def replaceCityNames(inData, country):
    retData = inData
    for city, rowI in inData.iterrows():
        for loggedCityName in getCities(country):
            #remove cities to be excluded here
            if city in excludeCities:
                retData = retData.drop([city])
            if cityNameMatch(city,loggedCityName) and not city in excludeCities:
                retData = retData.rename(index={city:loggedCityName})
    return retData


def getCities(country):
    return list(filter(lambda x: isinstance(x,str), countryCities[country]))

# do not include cityEntries that are:
# Null
# "Non-metropolitan areas"
# empty entries (":" or "Special")
# National Average values
# TODO: Verify with Vicky; separate cities that are joined using '-'
def filterCity(cityName):
    return not cityName == cityName or "Non-metropolitan" in cityName or ':' in cityName or "Special" in cityName or " - " in cityName or "National Average" in cityName


def splitCountries(rawData):
    countryTables = {}
    rawData = rawData.set_index('METROREG/TIME')
    unmatched = []
    filtered = []
    for cityName in list(rawData.index):
        # filter unwanted city entries       
        if filterCity(cityName): 
            filtered.append(cityName)
            continue
        if cityName in excludeCities:
            continue
        match = False
        for country in allCountries:
            for loggedCityName in getCities(country):
                if cityNameMatch(cityName,loggedCityName):
                    match = True
                    rawData = rawData.rename(index={cityName:loggedCityName})
                    if country not in countryTables:
                        countryTables[country] = rawData[loggedCityName:loggedCityName]
                    else:
                        countryTables[country] = countryTables[country].append(rawData[loggedCityName:loggedCityName])

                    break
            if(match): break
        if not match:
            unmatched.append(cityName)
    with open('filtered.txt', 'w+') as f:
        for item in filtered:
            f.write("%s\n" % item)

    # output the unmatched and filtered city names
    if not len(unmatched) == 0:
        errorMsg = "Could not match cities: "+ str(unmatched) + "\n see countryCities excel"
        # add nan to the rest of the unmatched list or countryCities dataframe to fit index length
        lenUnmatch = len(unmatched)
        lenCounCity = len(list(countryCities.index))
        if lenCounCity > lenUnmatch:
            for i in range(lenUnmatch,lenCounCity):
                unmatched.append(np.nan)    
            # add to "unmatched" column in countryCities
            countryCities['UNMATCHED'] = unmatched
            os.remove(fIn_CountryCities)
            countryCities.to_excel(fIn_CountryCities)

        elif lenUnmatch > lenCounCity:
            with open('unmatched.txt', 'w+') as f:
                for item in unmatched:
                    f.write("%s\n" % item)
        # throw error
        if "Connectivity" not in feat:
            raise Exception(errorMsg)
    return countryTables



### Read and Parse input file
dtypes = {'METROREG/TIME': str}
#for year in years:
#    dtypes = dtypes.update({year: float})

countryCities = pd.read_excel(fIn_CountryCities,dtypes=dtypes)
allCountries = countryCities.columns
if 'ALL' in includeCountries[0]:
    includeCountries = allCountries


print("Beginning... including countries: \n" + str(includeCountries))

outData = {}

for feat in feats:
    # open input file, specifying datatypes and which years to select
    inDataRaw = pd.read_excel(fIn_Data[feat],dtype=dtypes)   
    # split raw input into countries
    # inData: map: country name -> dataframe
    inData = splitCountries(inDataRaw)
    #if "gini" in feat:
    #    print(inData)

    for country in includeCountries:
        # Check if country is in data
        if not country in inData:
            exceptionMsg = ("WARNING! ... "+ country +" not found in input Datafile for "+feat)
            print(exceptionMsg)
            continue
        
        #merge only selected years of data
        if "GDP" in feat or "Population" in feat or "Patents" in feat:
            inData[country][feat] = inData[country][years].apply(merge, axis=1)

        # after combining/extracting data, remove other years
        inData[country] = inData[country][[feat]]
        # remove cities without data
        inData[country] = inData[country].dropna()
        # OBSELETE: Now done in splitCountry function
        # remove "Non-metropolitan regions in _"
        # for index,row in inData[country].iterrows():
        #    if "Non-metropolitan" in row['METROREG/TIME']:
        #        inData[country] = inData[country].drop(index,axis=0)

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
    for country in outData:
        outData[country].to_excel(writer, sheet_name=country)
