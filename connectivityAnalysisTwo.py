import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
### This script is a second try at running regressions of features vs connectivity


allCountries = ['Australia',
'Canada',
'Germany',
'Denmark',
'Spain',
'France',
"Netherlands",
'United Kingdom',
'Italy',
'Japan',
'Korea',
'United States']

feat = "GDP"

def getScaleParams(country, popList,featValList):
    pop = popList
    featVals = featValList
    #take log
    pop = list(map(lambda x: np.log(x), pop))
    featVals = list(map(lambda x: np.log(x), featVals))
    #plt.figure()
    #plt.plot
    print(pop,featVals)
    return np.polyfit(pop,featVals,1)


def getResiduals(Beta=0,logy0=0,pop=[],featValList=[]):
    residualList = []
    for x,y in zip(pop,featValList):
        residual = y - np.exp(logy0)*x**Beta
        residualList.append(residual)
    return residualList



data = {}
for country in allCountries:
    data[country] = pd.read_excel("Features2000_2005.xls",sheet_name=country)

Betas = {}
logy0s = {}
residuals = []
connectivities = []

for country in allCountries:
    countryData = data[country][["Population",feat,"Connectivity (asymmetric)"]].dropna()
    Betas[country],logy0s[country] = getScaleParams(country, countryData["Population"],countryData[feat])
    residuals = residuals + getResiduals(Beta=Betas[country],logy0=logy0s[country],pop=countryData["Population"],featValList=countryData[feat])
    connectivities = connectivities + list(countryData["Connectivity (asymmetric)"])

plt.figure()
plt.plot(connectivities,residuals,'bo')
plt.show()