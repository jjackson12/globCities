
import pandas as pd
import copy
import os
import numpy as np
import re
##### This script is to clean and organize data being used for characterization of city scaling properties




# run parameteres
# set true if you're just creating an initial empty dataFile
createEmptyData = False
# If multiple years are selected, the values are averaged into the output NOTE: 2015 and 2016 are only years with inequality data
years = ['2013','2014','2015','2016']
# spreadsheet connecting countries with cities
fIn_CountryCities = "CountryCities.xls"
# filenames of data source being cleaned, input
fIn_Data = "Data/OECDPopGDPMore.xlsx"
## Specifications for input datafile
# what does the spreadsheet label as cities? (e.g. METROREG/TIME)
cityLabel = 'Metropolitan Areas Name'
# what does the spreadsheet label as feature types (e.g. Variables Name)
featLabel = 'Variables Name'
# what does the spreadsheet label as country names (e.g. Metropolitan Areas -> US)
countryLabel = "Metropolitan Areas"
# map features to their type labels in data TODO: allow for selection of features to update
featTypeLabels = {
    'Population, All ages. Administrative data':'Population',
    'GDP (Millions USD, constant prices, constant PPP, base year 2010)':'GDP',
    'Disposable Income per equivalised household (in USD constant prices, constant PPP, base year 2010)':'Disposable Income per Household',
    'Gini (at disposable income, after taxes and transfers)':'Gini Index',
    'Unemployment (15 years old and over)':'Unemployment',
    'Poverty rate after taxes and transfers, Poverty line 60%':'Poverty Rate',
    'Air Pollution in PM2.5 (average level in µg/m³ experienced by the population)':'Air Pollution'
}

# some variables, when being compiled into joint MAs, should be added, while some should be averaged, etc
def compileCities(dPrior,dNew,feat):
    if feat=="Air Pollution" or feat=="Disposable Income per Household" or feat=='Gini Index' or feat=="Poverty Rate":
        return np.average([dPrior,dNew])
    elif feat =="GDP" or feat=="Population" or feat=="Unemployment":
        return dPrior + dNew
    

# filename of data source to be added to
fOut = "Features.xls"
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True
# list of countries to include. Either write "ALL" or give a list
includeCountries = ['ALL'] 
# cities to exclude due to aggregation into collective MAs.
excludeCities = []
# set to true if you want to overwrite the data already in fOut TODO
overwriteData = True


countryCodeToCountry = {
    'AUS':'Australia',
    'AT':'Austria',
    'BE':'Belgium',
    'CAN':'Canada',
    'CH':'Switzerland',
    'CL':'Chile',
    'COL':'Columbia',
    'CZ':'Czech Republic',
    'DE':'Germany',
    'DK':'Denmark',
    'ES':'Spain',
    'EE':'Estonia',
    'FI':'Finland',
    'FR':'France',
    'NL':"Netherlands",
    'UK':'United Kingdom',
    'EL':'Greece',
    'HU':'Hungary',
    'IE':'Ireland',
    'IS':'Iceland',
    'IT':'Italy',
    'JPN':'Japan',
    'KOR':'Korea',
    'LT':'Lithuania',
    'LU':'Luxembourg',
    'LV':'Latvia',
    'MEX':'Mexico',
    'NO':'Norway',
    'PL':'Poland',
    'PT':'Portugal',
    'SK':'Slovakia',
    'SI':'Slovenia',
    'SE':'Sweden',
    'USA':'United States'
}

def getCountryFromCode(countryCode):
    m = re.search('[A-Z]+',countryCode)
    return countryCodeToCountry[m.group(0)]


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
    #return not np.isnan(data)
    return (not np.isnan(dat)) #or isinstance(dat,int) or isinstance(dat,float))


# 2) once a match is found, update that country's data frame with that city's info
#     - if an entry for that city and property already exists, add the values
#     - Otherwise, update data
def updateFromRow(outData,loggedCityName,inRow,inCityName,country,foundMatch):
    retData = outData

    # if the city is not already in the country, add it here, with "UNKNOWN" tag
    if not foundMatch:
        inRow = inRow.rename({'Country':'UNKNOWN?'})
        inRow['UNKNOWN?'] = "UNKNOWN"
        retData[country] = retData[country].append(inRow)
        return retData
    feats = list(inRow.index)
    feats.remove("Country")
    for feat in feats:
        #if the data is already included in the output dataset, add to the already existing city entry
        if not np.isnan(retData[country][feat][loggedCityName]):
            print("adding "+inCityName+" to "+loggedCityName)
            retData[country][feat][loggedCityName] = compileCities(retData[country][feat][loggedCityName], inRow[feat], feat)
        #otherwise, just add it as a new city entry
        else:
            retData[country][feat][loggedCityName] = inRow[feat]
    return retData


# determine if two cities, with names potentially spelled differently and/or 
# in different languages, are the same cities. Cities with more than one way 
# of spelling will have them separated by '/'
def cityNameMatch(name1,name2):
    name1List = re.split('/|-',name1.lower().replace("(nuts 2010)",""))
    name2List = re.split('/|-',name2.lower().replace("(nuts 2010)",""))
    for subName1 in name1List:
        for subName2 in name2List:
            #if (subName1 in subName2 or subName2 in subName1) and not subName1.strip() == subName2.strip():
            #    print("edge case matching - %s , %s", (subName1, subName2))
            #if (subName1 in subName2) or (subName2 in subName1):
            if subName1.strip() == subName2.strip():
                return True
    return False



# read countryCities from fOut
countryCities = pd.read_excel(fIn_CountryCities)

allCountries = countryCities.columns
if 'ALL' in includeCountries[0]:
    includeCountries = allCountries

for country in includeCountries:
    countryCities[country] = pd.read_excel(fOut,sheet_name=country)['City']

### create empty output 
if createEmptyData:
    # this will be eventually printed as output
    # map: countryname to dataframe
    emptyData = {}




    # separate countryCities into different countries
    for country in includeCountries:
        emptyData[country] = pd.DataFrame(countryCities[country].dropna())
        emptyData[country] = emptyData[country].rename({country:'City'},axis='columns')
        #emptyData[country] = emptyData[country].set_index(country)
    # create output file with just cities, no data
    
    with  pd.ExcelWriter(fOut) as writer:
        for country in emptyData:
            emptyData[country].to_excel(writer, sheet_name=country,index=False)
        





### process data into one dataframe matching city-indices with country and properties
inDataRaw = pd.read_excel(fIn_Data,dtypes={cityLabel:str,countryLabel:str,featLabel:str})
inDataRaw = inDataRaw.set_index(cityLabel)

# set indices and columns for inData
cities = []
for city in list(inDataRaw.index):
    if city not in cities:
        cities.append(city)
columns = ["Country"] + list(featTypeLabels.values())
inData = pd.DataFrame(index=cities,columns=columns)
for cityName,rawDataRow in inDataRaw.iterrows():
    country = getCountryFromCode(rawDataRow[countryLabel])
    # the feature name as named in the input datafile
    feat = rawDataRow[featLabel]
    # calculate feature value from average over years
    featList = []
    for year in years:
        featList.append(rawDataRow[year])
    featVal = merge(featList)
    # update inData TODO: Only doing popuation???
    inData[featTypeLabels[feat]][cityName]=featVal
    inData["Country"][cityName] = country




### reformat city indicies/entries into standardized format
# iterate over every row in the dataframe, doing the following:
# 1) find a match for the cityName
#     - if no match exists, add it to "unmatched" output
# 2) once a match is found, update that country's data frame with that city's info
#     - if an entry for that city and property already exists, add the values

# start with (and later add to) existing dataframe from Features.xls
outData = {}
iterCountries = list(includeCountries) + ["UNKNOWN"]
for country in iterCountries:
    # TODO: Is setting index necessary? Will be different when starting vs updating
    if "UNKNOWN" in country:
        outData[country] = pd.DataFrame()
    else:
        outData[country] = pd.read_excel(fOut,sheet_name=country).set_index('City')
    # update with empty columns for new features
    for feat in featTypeLabels.values():
        # if overwriting, set existing data to NaN. If there's not data there, add empty column
        # TODO: move this to later stage, probably updateFromRow, so that entries that ARE NOT being updated 
        # are left alone (need extra parameter to hard overwrite everything)
        if (feat in outData[country].columns and overwriteData) or (feat not in outData[country].columns):
            outData[country][feat] = np.nan

for cityName, cityData in inData.iterrows():
    foundMatch = False
    country = cityData["Country"]
    # 1) find a match for the cityName
    for loggedCityName in list(outData[country].index):
        # check for matches with outData
        # skip over cities to be excluded here
        if cityNameMatch(cityName,loggedCityName) and not city in excludeCities:
            # 2) once a match is found, update that country's data frame with that city's info
            #     - if an entry for that city and property already exists, add the values
            #     - Otherwise, update data
            foundMatch = True
            outData = updateFromRow(outData,loggedCityName,cityData,cityName,country,foundMatch)
            break
    # if no match exists, add it to "unmatched" output
    if not foundMatch:
        outData = updateFromRow(outData,cityName,cityData,cityName,country,foundMatch)


# write each country data to dif
# ferent sheets in output
with pd.ExcelWriter("newFeatures.xls") as writer:
    for country in outData:
        outData[country].to_excel(writer, sheet_name=country)


# add to outData
#for country in countries:
#    for feat in feats:
#        outData[country][feat] = reformInData[country][feat]

# print output

