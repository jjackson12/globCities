import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
##### This script is to run basic scaling law analyses

### user configs
# input data file
fIn = "EUFeatures.xls"
#what features to analyze
feats = ["GDP","Patents","Connectivity"]#gini, Connectivity
# all countries with significant amounts of data
allCountries = ["United Kingdom","Germany","Spain","France","Netherlands","Italy","Poland","Romania"]
# what countries to analyze. 
countries = [["United Kingdom"]]
# Set true if you want to plot all possible countries individually
includeTag = 'ALL/SEPARATE' # this plots all countries on individual country plots
#includeTag = 'ALL/COMBINED' # this plots all countries together
#incldueTag = 'LIST' # this allows manual lists of countries in "countries" above
if includeTag == 'ALL/SEPARATE':
    countries = []
    #for country in allCountries:
    countries = list(map(lambda x: [x], allCountries))
elif includeTag == 'ALL/COMBINED':
    countries = [allCountries]
elif includeTag == 'LIST':
    countries = countries
else:
    print("WHAT COUNTRIES DO YOU WANT?")


# map, mapping countryname to dataframe
data = {}
# plot residuals vs connectivity
plotResiduals = True
# TODO: Include error bars





def getResiduals(pop,feat,Beta,y0):
    residuals = []
    for cityPop,cityFeat in zip(pop,feat):
        residual = cityFeat - (np.exp(y0)*(cityPop**Beta))
        residuals.append(residual)
    return residuals



def getData(countryList,features):
    retData = pd.DataFrame()
    for country in countryList:
        try:
            retData = retData.append(data[country][features].dropna())
        except KeyError as msg:
            errMsg = str(msg) + "for " + feat+", "+country
            print(errMsg)
    return retData

# returns Beta,y0 fit params
def getScaleParams(plotData,feat):
    #extract Population as x-axis and the feature you're analyzing as the y-axes, such as GDP
    pop = plotData["Population"]
    y = plotData[feat]
    # transform to log-log space
    if not "gini" in feat or "Connectivity" in feat:
        pop = np.array(list(map(lambda x: np.log(x), pop)))
        y = np.array(list(map(lambda x: np.log(x), y)))
    # fit to linear function, extract Beta and y_0
    return np.polyfit(pop, y, 1) 
    

for country in allCountries:
    data[country] = pd.read_excel(fIn,sheet_name=country)


#plot Beta vs. Connectivity, y0 vs. Connectivity
# NOTE: ONLY RUN THIS WITH INCLUDETAG = ALL/SEPARATE; DO NOT COMBINE COUNTRIES 
for feat in feats:
    countryBeta = []
    countryY0 = []
    countryConn = []
    for countryList in countries:
        # calculate average connectivity for each country
        try:
            connectivityData = getData(countryList,["Connectivity"])
            connectivity = np.average(list(connectivityData["Connectivity"])) 
            countryConn.append(connectivity)
        except KeyError as msg:
            print("in Beta vs. Connectivity, ",str(msg))
            continue
        #gather Beta and y0 values of each country
        plotData = getData(countryList,["Population",feat])
        Beta,y0 = getScaleParams(plotData,feat)
        countryBeta.append(Beta)
        countryY0.append(y0)



    #Beta,y0,connectivity = tuple(map(lambda x: (countryParams[x][0],countryParams[x][1],countryParams[x][2]), countryParams))

    # plot Beta vs connectivity for each country
    plt.figure()
    plt.plot(countryConn,countryBeta,'bo')
    plt.xlabel("Connectivity (avg per country)")
    plt.ylabel("Beta (of country)")
    ttl = "Beta vs. Connectivity for "+feat
    plt.title(ttl)
    outDir = "Figures/ConnectivityRelations"
    outName = outDir +"/countryBetas_"+feat +".png"
    plt.show()
    plt.savefig(outName)

    # plot y0 vs connectivity for each country
    plt.figure()
    plt.plot(countryConn,countryY0,'bo')
    plt.xlabel("Connectivity (avg per country)")
    plt.ylabel("Y_0 (of country)")
    ttl = "Y_0 vs. Connectivity for "+feat
    plt.title(ttl)
    outDir = "Figures/ConnectivityRelations"
    outName = outDir +"/countryY0s_"+feat +".png"
    plt.show()
    plt.savefig(outName)


#TODO: Clean up
# Standard Scaling Analysis
for feat in feats:
    for countryList in countries:
        plotData = getData(countryList,["Population",feat])

        # skip over countryLists without data
        if plotData.empty:
            msg = 'No Data for country {} and feature {}'.format(country,feat)
            print(msg)
            continue

        #extract Population as x-axis and the feature you're analyzing as the y-axes, such as GDP
        x_pop = plotData["Population"]
        y_feat = plotData[feat]

        # get scaling parameters
        Beta,y0 = getScaleParams(plotData,feat) 

        x_pop = np.array(list(map(lambda x: np.log(x), x_pop)))
        y_feat = np.array(list(map(lambda x: np.log(x), y_feat)))

        # plot standard scaling distributions
        plt.figure()
        plt.plot(x_pop, y_feat, 'bo')
        if Beta>1:
            lbl = "Superlinear: Beta = "+str(round(Beta,3))
        elif Beta<1:
            lbl = "Sublinear: Beta = "+str(round(Beta,3))
        else:
            lbl = "Linear, Beta = 1"

        # plot scaling fitting
        x_space = np.linspace(np.min(x_pop),np.max(x_pop),len(x_pop))
        plt.plot(x_space, Beta*x_space+y0, '--k',label=lbl)

        # plot null hypothesis linear fit
        plt.plot(x_space, x_space + np.min(x_pop)*Beta + y0 -np.min(x_pop), ':r',label="Linear Fit") 

        # create name for plot
        countryListName = ""
        for country in countryList:
            app = country + ", "
            countryListName = countryListName + (app)
        plotName = feat + " scaling for " + countryListName

        # create labels, legends, etc
        plt.title(plotName)
        plt.legend()
        if "gini" in feat or "Connectivity" in feat:
            plt.xlabel('Population')
        else:
            plt.xlabel('ln(Population)')
        if "gini" in feat or "Connectivity" in feat:
            yLab = feat
        else:
            yLab = "ln("+feat+")"
        plt.ylabel(yLab)
        #save to file
        countryListName = ""
        if includeTag == 'ALL/COMBINED':
            countryListName = "AllEU"
        else:
            for country in countryList:
                app = country + "-"
                countryListName = countryListName + (app)
        outDir = "Figures/ScalingFeatures"
        outName = outDir + "/" +countryListName[:-1]+"_"+feat+".png"
        plt.savefig(outName)

        # Connectivity Analysis
        if plotResiduals and not "Connectivity" in feat:
            # plot residuals. Skip if there's no Connectivity Data
            connectivityData = pd.DataFrame()
            for country in countryList:
                try:
                    connectivityData = connectivityData.append(data[country][["Population",feat,"Connectivity"]].dropna())
                except KeyError as msg:
                    errMsg = str(msg) + "for " + feat+", "+country
                    print(errMsg)
            #skip over if country has no Connectivity data
            try:
                connectivity = connectivityData["Connectivity"]
            except KeyError:
                continue
            residuals = getResiduals(connectivityData["Population"],connectivityData[feat],Beta,y0)
            plt.figure()
            plt.plot(connectivity,residuals,'bo')
            plt.xlabel('Connectivity')
            plt.ylabel("deviation from scaling expectation")
            ttl = feat + " vs. Connectivity"
            plt.title(ttl)
            outDir = "Figures/ConnectivityRelations"
            outName = outDir + "/" + countryListName[:-1]+"_"+feat+"_Connectivity.png"
            plt.savefig(outName)
            