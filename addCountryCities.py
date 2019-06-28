import pandas as pd
import copy
import os
import numpy as np
import re
### This script is meant to help process new large datasets from many countries 
### by updating the mapping of countries to cities in countryCities.xls
countryCodesLabel = 'Metropolitan Areas'
cityNamesLabel = 'Metropolitan Areas Name'

df = pd.read_excel('Data/ObservationData_wzlficb.xlsx',dtypes={countryCodesLabel:str,cityNamesLabel:str})

countryCodes = df[countryCodesLabel]
cityNames = df[cityNamesLabel]

fNew = 'CountryCitiesNew.xls'


# read countryCities
countryCities = pd.read_excel("CountryCities.xls")
includedCountries = countryCities.columns

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

inputCountryCities = {}
for countryCode,cityName in zip(countryCodes,cityNames):
    country = getCountryFromCode(countryCode)
    if not country in inputCountryCities:
        inputCountryCities[country] = [cityName]
    else:
        if cityName not in inputCountryCities[country]:
            inputCountryCities[country].append(cityName)


for country in inputCountryCities:
    if not country in includedCountries:
        countryCities[country] = pd.DataFrame(inputCountryCities[country]).rename({0:country},axis='columns')[country]
    # NOTE: add new cities; not implemented because the existing EU cities are from the same datset
    # else:
        #for city in inputCountryCities[country]:

countryCities.to_excel(fNew,index=False)
#for country in country:
#    with  pd.ExcelWriter(fNew) as writer:
#        for country in countryCities:
#            countryCities[country].to_excel(writer, sheet_name=country,index=False)
            
