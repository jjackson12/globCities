import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
##### This script is to run basic scaling law analyses

### user configs
# input data file
fIn = "Features2000_2005.xls"
#what features to analyze
feats = ["GDP","Unemployment"]
# feats to be plotted on a linear regression rather than log-log
linearFeats = ["Gini index", "Poverty Rate"]
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

# what countries to analyze. 
countries = [["United Kingdom", "United States","Germany","France","Canada","Australia"]]
# minimum number of datapoints to plot
dataPlotMin = 7
# what type of connectivity to use for residual plotting
connectivityTag = "Connectivity (symmetric)"
# Set true if you want to plot all possible countries individually
#includeTag = 'ALL/SEPARATE' # this plots all countries on individual country plots
includeTag = 'ALL/COMBINED' # this plots all countries together
#includeTag = 'ALL/COMBINED+SEPARATE' # this plots each country individually plus all of EU as one (TODO: Not yet implemented)
#includeTag = 'LIST' # this allows manual lists of countries in "countries" above
# plot residuals vs connectivity
plotResiduals = True
# plot scaling relations
plotScaling = False




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

# TODO: Include error bars







def getResiduals(pop,feat,Beta,y0,featMean=1):
    residuals = []
    for cityPop,cityFeat in zip(pop,feat):
        residual = cityFeat - (np.exp(y0)*(cityPop**Beta))
        # normalize by mean of that country's feature
        residual = residual/featMean
        residuals.append(residual)
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


def getDataFromList(countryList,features):
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
    if not feat in linearFeats:
        pop = np.array(list(map(lambda x: np.log(x), pop)))
        y = np.array(list(map(lambda x: np.log(x), y)))
    # fit to linear function, extract Beta and y_0
    return np.polyfit(pop, y, 1) 
    

for country in allCountries:
    data[country] = pd.read_excel(fIn,sheet_name=country)


#plot Beta vs. Connectivity, y0 vs. Connectivity
# NOTE: ONLY RUN THIS WITH INCLUDETAG = ALL/SEPARATE; DO NOT COMBINE COUNTRIES 
if False:
    for feat in feats:
        countryBeta = []
        countryY0 = []
        countryConn = []
        for countryList in countries:
            # calculate average connectivity for each country
            try:
                connectivityData = getDataFromList(countryList,["Connectivity (normalized)"])
                connectivity = np.average(list(connectivityData["Connectivity (normalized)"])) 
                countryConn.append(connectivity)
            except KeyError as msg:
                print("in Beta vs. Connectivity, ",str(msg))
                continue
            #gather Beta and y0 values of each country
            plotData = getDataFromList(countryList,["Population",feat])
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
        #plt.show()
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
        #plt.show()
        plt.savefig(outName)


#TODO: Clean up
# Standard Scaling Analysis
if plotScaling:
    for feat in feats:
        for countryList in countries:
            plotData = getDataFromList(countryList,["Population",feat])

            # skip over countryLists without data
            if plotData.empty:
                msg = 'No Data for country {} and feature {}'.format(country,feat)
                print(msg)
                continue
                
            # skip over countryLists with less than a set number of datapoints
            if len(list(plotData.index)) < dataPlotMin:
                msg = 'Not Enough Data for country {} and feature {}'.format(country,feat)
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
            if feat in linearFeats:
                plt.xlabel('Population')
                yLab = feat
            else:
                plt.xlabel('ln(Population)')
                yLab = "ln("+feat+")"
            plt.ylabel(yLab)
            #save to file
            countryListName = ""
            if includeTag == 'ALL/COMBINED':
                countryListName = "AllCountries"
            else:
                for country in countryList:
                    app = country + "-"
                    countryListName = countryListName + (app)
            outDir = "Figures/ScalingFeatures"
            outName = outDir + "/" +countryListName[:-1]+"_"+feat+".png"
            plt.savefig(outName)






# Connectivity Analysis
# plot residuals. Skip if there's no Connectivity Data
if plotResiduals:
    for feat in feats:

        if connectivityTag in feat:
            continue
        
        residuals = []
        connectivities = []

        # for each country SEPARATELY, run fits on scaling relations to get residuals, collect with connectivity data
        # TODO: What about countries being plotted on linear-linear plot?
        for countryList in countries:
            for country in countryList:
                plotData = data[country][["Population",feat,connectivityTag]].dropna()

                # skip over countryLists without data
                if plotData.empty:
                    msg = 'No Data for country {} and feature {}'.format(country,feat)
                    print(msg)
                    continue
                    
                # skip over countryLists with less than a set number of datapoints
                if len(list(plotData.index)) < dataPlotMin:
                    msg = 'Not Enough Data for country {} and feature {}'.format(country,feat)
                    print(msg)
                    continue
            
                # get scaling parameters
                Beta,y0 = getScaleParams(plotData,feat) 

                feats = list(plotData[feat])
                residuals = residuals + getResiduals(plotData["Population"],feats,Beta,y0,featMean=np.average(feats))
                connectivities = connectivities + list(plotData[connectivityTag])
        
            if len(residuals) == 0:
                continue
            # TODO Label different countries differently, make residuals & connectivities into maps indexed by countries
            plt .figure()
            # 
            #residuals = connScale(residuals)
            plt.plot(connectivities,residuals,'bo')
            plt.xlabel('Connectivity')
            plt.ylabel("deviation from scaling expectation")
            ttl = feat + " vs. Connectivity"
            plt.title(ttl)
            outDir = "Figures/ConnectivityRelations"
            if includeTag == 'ALL/COMBINED':
                countryListName = "AllCountriess"
            else:
                for country in countryList:
                    app = country + "-"
                    countryListName = countryListName + (app)
            outName = outDir + "/" + countryListName[:-1]+"_"+feat+"_"+connectivityTag+".png"
            #outName = outDir + "/LargeCountries_" + feat+ "_Connectivity"
            plt.savefig(outName)
