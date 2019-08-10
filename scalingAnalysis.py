import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as sk
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from RegscorePy import *
##### This script provides helper functions for analyzing pre-processed datasets

# all countries with significant amounts of data
allCountries = ['Australia',
'Austria',
'Belgium',
'Canada',
'Switzerland',
'Chile',
'Colombia',
'Czech Republic',
'Germany',
'Denmark',
'Spain',
'Estonia',
'Finland',
'France',
"Netherlands",
'United Kingdom',
'Greece',
'Hungary',
'Ireland',
'Iceland',
'Italy',
'Japan',
'Korea',
'Lithuania',
'Luxembourg',
'Latvia',
'Mexico',
'Norway',
'Poland',
'Portugal',
'Slovakia',
'Slovenia',
'Sweden',
'United States']

resCalc = "SAMI"

def getAllCountries():
    return allCountries



# NOTE: y0 is actually log(y0), which is what getScaleParams returns
# TODO: Fix this for later
def getResiduals(pop,feat,Beta,y0,featMean=1,manResCalc=resCalc):
    residuals = []
    for cityPop,cityFeat in zip(pop,feat):
        ## ratio
        if manResCalc=="ratio":
            residual = cityFeat/(y0*(cityPop**Beta))
        elif manResCalc=="diff":
            ## difference
            residual = cityFeat - (y0*(cityPop**Beta))
            # normalize by mean of that country's feature
            residual = residual/featMean
        elif manResCalc=="SAMI":
            #logMean = np.average(np.log(feat))
            #if logMean < 0 :
            #    logMean = logMean*-1
            residual = np.log(cityFeat/(y0*(cityPop**Beta)))
        else:
            raise Exception("NO RESIDUAL CALCULATION GIVEN")
        residuals.append(residual)
        if residual < -10:
            print(cityPop)
            print(cityFeat)
    return residuals



def connScale(residuals):
    res = np.array(residuals)
    minVal = np.min(res)
    if np.min(res) > 0:
        raise Exception("no underperformance")
    #reset so worst performance will be zero, everything scaling up from there
    res = res - minVal + 1
    res = np.log(res)
    res = res - np.log(-minVal+1)
    res = res/np.max(res)
    print(np.min(res))
    return list(res)

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


def getDataFromList(data,countryList,features):
    retData = pd.DataFrame()
    for country in countryList:
        try:
            retData = retData.append(data[country][features].dropna())
        except KeyError as msg:
            errMsg = str(msg) + "for " + feat+", "+country
            print(errMsg)
    return retData

# returns Beta, y0 fit params
def getScaleParams(plotData,feat,linearFeats):
    #extract Population as x-axis and the feature you're analyzing as the y-axes, such as GDP
    pop = plotData["Population"]
    y = plotData[feat]
    # transform to log-log space
    if not feat in linearFeats:
        pop = np.array(list(map(lambda x: np.log(x), pop)))
        y = np.array(list(map(lambda x: np.log(x), y)))
    # fit to linear function, extract Beta and y_0
    Beta,y0 = np.polyfit(pop, y, 1) 
    return Beta, np.exp(y0)
    


def getNetConnectivities(connectivityTags,connData,manResCalc=resCalc):
    finalConnectivities = np.zeros(len(connData.index))
    for connectivityTag in connectivityTags.keys():
        finalConnectivities = finalConnectivities + connectivityTags[connectivityTag] * np.array(connData[connectivityTag])
    # for considering connectivity as deviation from scaling expectation of connectivity
    BetaC,y0C = np.polyfit(np.log(connData["Population"]),np.log(finalConnectivities),1)
    return getResiduals(connData["Population"],finalConnectivities,BetaC,np.exp(y0C),featMean=np.average(finalConnectivities),manResCalc= manResCalc)