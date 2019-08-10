
import pandas as pd
import copy
import os
import numpy as np
import re
##### This script is to clean and organize data being used for characterization of city scaling properties




# run parameteres
# set true if you're just creating an initial empty dataFile
createEmptyData = False

# update dataFile cityNames from one file to another
updateCityNames = False
# file with most up-to-date city names
fUpdated = "Features2013_2016.xls"
# file to be updated
fToUpdate = "Features2000_2005.xls"

# If multiple years are selected, the values are averaged into the output NOTE: 2015 and 2016 are only years with inequality data
years = ["2000","2001","2002","2003","2004","2005"]
# filenames of data source being cleaned, input
fIn_Data = "Data/ConnectivitiesNew.xls"
# filename of country-cities mapping sheet NOTE: Not updated
fIn_countryCities = "CountryCities"
## Specifications for input datafile
# what does the spreadsheet label as cities? (e.g. METROREG/TIME)
cityLabel = 'Cities'
# what does the spreadsheet label as feature types (e.g. Variables Name)
featLabel = 'Presence times Degree'
# what does the spreadsheet label as country names (e.g. Metropolitan Areas -> US)
countryLabel = "Metropolitan Areas"
# map features to their type labels in data TODO: allow for selection of features to update
featTypeLabels = {
   #'':'Air Traffic'
   'Presence times Degree':'Connectivity (Presence times Degree)'

     #'Connectivity (normalized)':'Global Firm Presence (without Connectivity)'
#    'Population, All ages. Administrative data':'Population',
#    'GDP (Millions USD, constant prices, constant PPP, base year 2010)':'GDP',
#    'Disposable Income per equivalised household (in USD constant prices, constant PPP, base year 2010)':'Disposable Income per Household',
#    'Gini (at disposable income, after taxes and transfers)':'Gini Index',
#    'Unemployment (15 years old and over)':'Unemployment',
#    'Poverty rate after taxes and transfers, Poverty line 60%':'Poverty Rate',
#    'Air Pollution in PM2.5 (average level in µg/m³ experienced by the population)':'Air Pollution'
}
# if you want to remove features existing in fOut, write their column names here
removeFeats = []

# some variables, when being compiled into joint MAs, should be added, while some should be averaged, etc
def compileCities(dPrior,dNew,feat):
    if feat=="Connectivity" or feat=="Air Pollution" or feat=="Disposable Income per Household" or feat=='Gini Index' or feat=="Poverty Rate":
        return np.average([dPrior,dNew])
    elif feat =="GDP" or feat=="Population" or feat=="Unemployment" or feat=="Air Traffic":
        return dPrior + dNew
    

# filename of data source to be added to
fOut = "Features2000_2005.xls"
# if True, include cities in the input dataset that are NOT in the old (compiled) dataset
addPartialData = True
# list of countries to include. Either write "ALL" or give a list
includeCountries = ['ALL'] 
# cities to exclude due to aggregation into collective MAs.
excludeCities = []
# set to true if you want to overwrite the data already in fOut TODO
overwriteData = True
# set true if you're running on a Knomea Dataset
KnoemaRun = False
# set true if the data you're analyzing is organized by year
timeSeries = False


countryCodeToCountry = {
    'AUS':'Australia',
    'AT':'Austria',
    'BE':'Belgium',
    'CAN':'Canada',
    'CH':'Switzerland',
    'CL':'Chile',
    'COL':'Colombia',
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
    return not (isinstance(dat,str) or np.isnan(dat))# or isinstance(dat,int) or isinstance(dat,float))


# 2) once a match is found, update that country's data frame with that city's info
#     - if an entry for that city and property already exists, add the values
#     - Otherwise, update data
def updateFromRow(outData,loggedCityName,inRow,inCityName,country,foundMatch):
    retData = outData

    # if the city is not already in the country, add it here, with "UNKNOWN" tag
    if not foundMatch:
        if KnoemaRun:
            inRow = inRow.rename({'Country':'UNKNOWN?'})
            inRow['UNKNOWN?'] = "UNKNOWN"
            retData[country] = retData[country].append(inRow)
        else:
            retData["UNKNOWN"] = retData["UNKNOWN"].append(inRow)
        return retData
    feats = list(inRow.index)
    if KnoemaRun:
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


# do not include cityEntries that are:
# Null
# "Non-metropolitan areas"
# empty entries (":" or "Special")
# National Average values
# "UNKNOWN", as designated in airport-city conversions in function citiesFromAirports
def filterCity(cityName):
    return not cityName == cityName or "Non-metropolitan" in cityName or ':' in cityName or "Special" in cityName or " - " in cityName or "National Average" in cityName

# TODO: Finish manually cleaning the excel sheet. NEED TO GO THROUGH MORE THOROUGHLY. 
# Look into Pau/Tarbes to see how the Metropolitan Areas are defined
# From there, go through each entry to carefully categorize the airports. While doing so,
# make it extendable in the countryCities spreadsheet so I NEVER have to repeat this later

# manual mappings for weird inputs
airportCityMappings = {
    "LONDON HEATHROW": "London",
    "LONDON GATWICK": "London",
    "LONDON STANSTED": "London",
    "LYON SAINT-EXUPERY": "Lyon",
    "NANTES ATLANTIQUE":"Nantes",
    "LEEDS BRADFORD":"Leeds",
    "BEOGRAD/NIKOLA TESLA":"Belgrade",
    "MONTPELLIER MEDITERRANEE":"Montpellier",
    "PARIS system":"Paris"
}

# given airport, the name of an airport-city pair, return the city that airport is in
def cityFromAirport(airport):
    if "Unknown airport" in airport or "Other airport" in airport:
        return "UNKNOWN"
    else:
        airport = airport.replace(" airport","").replace("/INTL","").replace("/INTERNATIONAL","")
        if airport in airportCityMappings.keys():
            print("caught {}, turning into {}".format(airport, airportCityMappings[airport]))
            return airportCityMappings[airport]
        else:
            return airport
        #TODO: Double check

# airportData: list of city-airport labels from Eurostat dataset of city air traffic, e.g. "PRAHA/RUZYNE airport"
# returns the data with renamed indices
def citiesFromAirports(airportData):
    retData = airportData
    for airportName in list(airportData.index):
        cityName = cityFromAirport(airportName)
        if "UNKNOWN" in cityName and airportName in list(retData.index):
                retData = retData.drop(airportName)
        # merge if the cityName already exists
        elif cityName in list(retData.index):
            print(cityName)
            retData.loc[cityName] = retData.loc[cityName] + airportData.loc[airportName]
            if airportName in list(retData.index):
                retData = retData.drop(airportName)
        else:
            retData = retData.rename(index={airportName:cityName})
    return retData

# split all cities in rawData into their respective countries
def splitCountries(rawDataIn,outData,feat=''):
    # map: countryName -> Dataframe of cities in that country
    countryTables = outData
    rawData = rawDataIn

    # airport names have to be renamed to their respective cities 
    if "Air Traffic" in feat:
        rawData = rawData.dropna(how='all')
        rawData = citiesFromAirports(rawData)

    for cityName in list(rawData.index):
        match = False
        for country in list(countryTables.keys()):
            for loggedCityName in list(countryTables[country].index):
                # if the cities match, do the following:
                if cityNameMatch(cityName,loggedCityName):
                    match = True    
                    countryTables = updateFromRow(countryTables,loggedCityName,rawData.loc[cityName],cityName,country,match)
                    break

            if(match): break
        if not match:
            countryTables = updateFromRow(countryTables,cityName,rawData.loc[cityName],cityName,"UNKNOWN",match)

    return countryTables




# determine if two cities, with names potentially spelled differently and/or 
# in different languages, are the same cities. Cities with more than one way 
# of spelling will have them separated by '/'
def cityNameMatch(name1,name2):
    newNames = []
    for name in [name1,name2]:
        newName = name.lower()
        newName = newName.replace("(nuts 2010)","")
        newName = newName.replace("greater ","")
        newName = newName.replace(" (greater)","")
        newNameList = re.split('/|-',newName)
        newNames.append(newNameList)
        
    name1List = newNames[0]
    name2List = newNames[1]
    for subName1 in name1List:
        for subName2 in name2List:
            #if (subName1 in subName2 or subName2 in subName1) and not subName1.strip() == subName2.strip():
            #    print("edge case matching - %s , %s", (subName1, subName2))
            #if (subName1 in subName2) or (subName2 in subName1):
            if subName1.strip() == subName2.strip():
                return True
    return False











# read countryCities from fOut
fOutData = pd.ExcelFile(fOut)

allCountries = fOutData.sheet_names  # see all sheet names

if 'ALL' in includeCountries[0]:
    includeCountries = allCountries


### update city names
if updateCityNames:
    updatedData = {}
    toUpdateData = {}
    for country in allCountries:
        if country in "UNKNOWN":
            continue

        updatedData[country] = pd.read_excel(fUpdated,sheet_name=country).set_index(cityLabel)
        toUpdateData[country] = pd.read_excel(fToUpdate,sheet_name=country).set_index(cityLabel)

        updatedCityNames = list(updatedData[country].index)
        toUpdateCityNames = list(toUpdateData[country].index)

        toUpdateData[country] = toUpdateData[country].rename(index=dict(zip(toUpdateCityNames,updatedCityNames)))

        # for testing
        fToUpdateTest = "testUpdate.xls"



    with pd.ExcelWriter(fToUpdate) as writer:
        for country in allCountries:
            if not country in "UNKNOWN":
                toUpdateData[country].to_excel(writer,sheet_name=country)






### create empty output 
if createEmptyData:
    # this will be eventually printed as output
    # map: countryname to dataframe
    emptyData = {}
    countryCities = pd.read_excel(fIn_countryCities)




    # separate countryCities into different countries
    for country in includeCountries:
        emptyData[country] = pd.DataFrame(countryCities[country].dropna())
        emptyData[country] = emptyData[country].rename({country:'City'},axis='columns')
        #emptyData[country] = emptyData[country].set_index(country)
    # create output file with just cities, no data
    
    with  pd.ExcelWriter(fOut) as writer:
        for country in emptyData:
            emptyData[country].to_excel(writer, sheet_name=country,index=False)
        

if not updateCityNames:
    # start with (and later add to) existing dataframe from Features.xls
    outData = {}
    iterCountries = list(includeCountries)
    if "UNKNOWN" in iterCountries:
        iterCountries.remove("UNKNOWN")

    for country in iterCountries:
        # TODO: Is setting index necessary? Will be different when starting vs updating
        outData[country] = pd.read_excel(fOut,sheet_name=country).set_index('City')

        # drop nan-index entries
        outData[country] = outData[country][outData[country].index.notnull()]

        # update with empty columns for new features
        for feat in featTypeLabels.values():
            # if overwriting, set existing data to NaN. If there's not data there, add empty column
            # TODO: move this to later stage, probably updateFromRow, so that entries that ARE NOT being updated 
            # are left alone (need extra parameter to hard overwrite everything)
            if (feat in outData[country].columns and overwriteData) or (feat not in outData[country].columns):
                outData[country][feat] = np.nan
        
        # remove features as specified above
        try:
            outData[country] = outData[country].drop(columns=removeFeats)
        except KeyError:
            print("WARNING: Attempting to remove feature(s) that are not in the dataset: "+str(removeFeats))
            continue

    # standard processing for most datasets
    if not KnoemaRun:
        # add unknown as new sheet for non-country-marked data (not Knoema)
        columns = featTypeLabels.values()
        outData["UNKNOWN"] = pd.DataFrame(columns = columns)
        dtypes = {cityLabel:str}

        # open input file, merging arrivals and departures for air traffic
        # TODO: Go back and make this work, combining arrivals and departures
        #if "Air Traffic" in feat:
        #    arrivals = pd.read_excel(fIn_Data,dtype=dtypes,sheet_name="EUArrivals")
        #    arrivals = arrivals.set_index(cityLabel)
        #    departures = pd.read_excel(fIn_Data,dtype=dtypes,sheet_name="EUDepartures")
        #    departures = departures.set_index(cityLabel)
        #    inDataRaw = (arrivals + departures)/2
        #else:
        #    inDataRaw = pd.read_excel(fIn_Data,dtype=dtypes)   
        #    inDataRaw = inDataRaw.set_index(cityLabel)
        if "Air Traffic" in feat:
            inDataRaw = pd.read_excel(fIn_Data,dtype=dtypes,sheet_name="EUArrivals")
        else:
            inDataRaw = pd.read_excel(fIn_Data,dtype=dtypes)   
        inDataRaw = inDataRaw.set_index(cityLabel)

        if timeSeries:
        # combine different years of Data
            for feat in list(featTypeLabels.values()):
                inDataRaw[feat] = inDataRaw[years].apply(merge, axis=1)
            inDataRaw = inDataRaw[list(featTypeLabels.values())]
            



        inDataRaw = inDataRaw.rename(columns=featTypeLabels)
                
                #merge only selected years of data for EuroStat data 


        #TODO: I don't think this needs to iterate over features; should run one time, with upDateFromRow
        # properly moving all data over 
        for featLbl in list(featTypeLabels.keys()):
            feat = featTypeLabels[featLbl]

            # split raw input into countries
            # inData: map: country name -> dataframe
            outData = splitCountries(inDataRaw,outData,feat=feat)



    # TODO: Tokyo Population HUGE
    # different processing for Knomean datasets
    elif KnoemaRun: 
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


