import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as sk
from scipy.optimize import curve_fit
from RegscorePy import *
##### This script is to run basic scaling law analyses

### user configs
years = "2000-2005"
# input data file
fIn = "Features"+years.replace("-","_")+".xls"
#what features to analyze
feats = ["GDP","Disposable Income per Household","Unemployment"]
# feats to be plotted on a linear regression rather than log-log
linearFeats = ["Gini Index"]
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
#countries = [["United Kingdom"]]
countries = [[#'Australia',
#'Canada',
#'Germany',
#'Spain',
#'France',
'United Kingdom',
#'Italy',
#'United States'
]]
# minimum number of datapoints to plot
dataPlotMin = 7
# what type of connectivity to use for residual plotting
connectivityTags = {
    "Connectivity (asymmetric)":0.5,
    "Connectivity (symmetric)":0.5#,
    #"Air Traffic":0.33
}

# what to call this combination of connectivities in output file
connectivityLbl = "BothFirmConnectivities"
# Set true if you want to plot all possible countries individually#
includeTag = 'ALL/SEPARATE' # this plots all countries on individual country plots
#includeTag = 'ALL/COMBINED' # this plots all countries together
#includeTag = 'ALL/COMBINED+SEPARATE' # this plots each country individually plus all of EU as one (TODO: Not yet implemented)
#includeTag = 'LIST' # this allows manual lists of countries in "countries" above
# plot residuals vs connectivity
plotResiduals = False
# plot scaling relations
plotScaling = False
# try borrowed size fit with air traffic
borrowedSizeFit = True
# calculate residuals using difference ("diff") or ratio ("ratio") TODO: or "SAMI"
resCalc = "ratio"


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
        ## ratio
        if resCalc=="ratio":
            residual = cityFeat/(np.exp(y0)*(cityPop**Beta))
        elif resCalc=="diff":
            ## difference
            residual = cityFeat - (np.exp(y0)*(cityPop**Beta))
            # normalize by mean of that country's feature
            residual = residual/featMean
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

# NOTE: OLD UNUSED CODE
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

        outDir = "Figures/ConnectivityRelations/"+years
        outName = outDir +"/countryBetas_"+feat +".png"
        #plt.show()
        plt.savefig(outName)
        plt.close()

        # plot y0 vs connectivity for each country
        plt.figure()
        plt.plot(countryConn,countryY0,'bo')
        plt.xlabel("Connectivity (avg per country)")
        plt.ylabel("Y_0 (of country)")
        ttl = "Y_0 vs. Connectivity for "+feat
        plt.title(ttl)
        outDir = "Figures/ConnectivityRelations/"+years
        outName = outDir +"/countryY0s_"+feat +".png"
        #plt.show()
        plt.savefig(outName)
        plt.close()


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

            # TODO: Change to a log scale in plot, not in variables; also change fitting function here to match
            if not feat in linearFeats:
                x_pop = np.array(list(map(lambda x: np.log(x), x_pop)))
                y_feat = np.array(list(map(lambda x: np.log(x), y_feat)))


            # plot standard scaling distributions

            countryListName = ""
            if includeTag == 'ALL/COMBINED':
                countryListName = "AllCountries"
            else:
                for country in countryList:
                    app = country + "-"
                    countryListName = countryListName + (app)
            outDir = "Figures/ScalingFeatures/"+years
            outName = outDir + "/" +countryListName[:-1]+"_"+feat+".png"

            plt.figure(outName)
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

            # plot null hypothesis linear fit TODO: Something went funky here, maybe check
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

            plt.savefig(outName)
            plt.close()






# Connectivity Analysis
# plot residuals. Skip if there's no Connectivity Data
if plotResiduals:
    # do analysis seperately for every feature
    for feat in feats:

        # ignore connectivity vs connectivity
        skip = False
        for connectivityTag in connectivityTags.keys(): 
            if connectivityTag in feat:
                skip = True
                continue
        if skip:
            continue


        # TODO: What about countries being plotted on linear-linear plot?
        # for every set of countries to plot together, reset residuals and connectivities to be plotted together
        for countryList in countries:
            residuals = []
            connectivities = []
            # for each country SEPARATELY, run fits on scaling relations to get residuals, collect with connectivity data
            for country in countryList:
                dataToPull = ["Population",feat]
                for connectivityTag in connectivityTags.keys():
                    dataToPull.append(connectivityTag)
                plotData = data[country][dataToPull].dropna()

                # skip over countryLists without data
                if plotData.empty:
                    msg = 'No Data for country {} and feature {}'.format(country,feat)
                    #print(msg)
                    continue
                    
                # skip over countryLists with less than a set number of datapoints
                if len(list(plotData.index)) < dataPlotMin:
                    msg = 'Not Enough Data for country {} and feature {}'.format(country,feat)
                    #print(msg)
                    continue
            
                print("fitting ",country)
                # get scaling parameters
                Beta,y0 = getScaleParams(plotData,feat) 
                #plt.figure()
                ## sanitycheck for fittings
                # pop = list(plotData["Population"])
                # plt.plot(list(map(lambda x: np.log(x),pop)),list(map(lambda x: np.log(x),list(plotData[feat]))), 'ro')
                # x_space = np.linspace(np.log(np.min(pop)),np.log(np.max(pop)),len(pop))
                # plt.plot(x_space, Beta*x_space+y0, '--k')
                # plt.show()
                # plt.close()
                feats = list(plotData[feat])

                residuals = residuals + getResiduals(plotData["Population"],feats,Beta,y0,featMean=np.average(feats))

                newConnectivities = {}
                finalConnectivities = np.zeros(len(feats))
                for connectivityTag in connectivityTags.keys():
                    # for considering connectivity as deviation from scaling expectation of connectivity
                    BetaC,y0C = getScaleParams(plotData,connectivityTag)
                    newConnectivities[connectivityTag] = connectivityTags[connectivityTag] * np.array(getResiduals(plotData["Population"],plotData[connectivityTag],BetaC,y0C,featMean=np.average(list(plotData[connectivityTag]))))
                    finalConnectivities = finalConnectivities + newConnectivities[connectivityTag]

                    
                connectivities = connectivities + list(finalConnectivities)#list(plotData[connectivityTag])
        
            if len(residuals) == 0:
                continue
            
            outDir = "Figures/ConnectivityRelations/"+years
            countryListName = ""
            if includeTag == 'ALL/COMBINED':
                countryListName = "AllCountriess"
            else:
                for country in countryList:
                    app = country + "-"
                    countryListName = countryListName + (app)
            

            outName = outDir + "/" + countryListName[:-1]+"_"+feat+"_"+connectivityLbl+ "_"+resCalc+ ".png"
            #outName = outDir + "/AllCountries_" + feat+ "_Connectivity"
            # TODO Label different countries differently, make residuals & connectivities into maps indexed by countries
            plt.figure(outName)
            # 
            #residuals = connScale(residuals)
            plt.loglog(connectivities,residuals,'bo')
            xLbl = "deviation in " +connectivityLbl+" ("+resCalc+")"
            yLbl = "deviation in "+feat+" ("+resCalc+")"
            plt.xlabel(xLbl)
            plt.ylabel(yLbl)
            ttl = feat + " vs. "+connectivityLbl
            plt.title(ttl)

            plt.savefig(outName)
            plt.close()





def borrowedSizeModel(x,y0,Beta,Alpha):
    #print(str(x))
    return y0*(x[:,0]+x[:,1]*Alpha)**Beta

def standardModel(x,y0,Beta):
    return y0*(x)**Beta


# Borrowed size fitting Analysis
if borrowedSizeFit:
    # do analysis seperately for every feature
    
    for feat in feats:
        # ignore connectivity vs connectivity
        skip = False
        for connectivityTag in connectivityTags.keys(): 
            if connectivityTag in feat:
                skip = True
                continue
        if skip:
            continue

        Alphas = {}
        R2Ratios = {}
        aicRatios = {}

        #FIXME: error with running all countries
        for countryList in countries:
            plotData = getDataFromList(countryList,["Population",feat,"Air Traffic"])

            # skip over countryLists without data
            if plotData.empty:
                msg = 'No Data for country {} and feature {}'.format(country,feat)
                #print(msg)
                continue
                
            # skip over countryLists with less than a set number of datapoints
            if len(list(plotData.index)) < dataPlotMin:
                msg = 'Not Enough Data for country {} and feature {}'.format(country,feat)
                #print(msg)
                continue
        
            print("fitting for R^2 ",str(countryList))
            print("feat, ",feat)

            pop = plotData["Population"]
            featVals = plotData[feat]
            aTraffic = plotData["Air Traffic"]

            #guess = ()
            # standard scaling parameters
            guess = (1,featVals[0]/pop[0])
            (y0,Beta), pcov = curve_fit(standardModel,pop,featVals,guess)


            concatData = []

         
            for a,b in zip(pop,aTraffic):
                concatData.append((a,b))
            #FIXME: Fix ordering
            #dtype = [('pop', float), ('aTraffic', float)]
            #concatData = np.array(concatData,dtype=dtype)
            #concatData = np.sort(concatData, order='pop')

            concatData = np.array(concatData)
            #concatData = list(map(lambda x: list(x), list(concatData)))
            #print

            guess = (y0,Beta,1/1000)
            params, pcov = curve_fit(borrowedSizeModel,concatData[:,:2],featVals,guess)
            y0BF,BetaBF,AlphaBF = params


            noBorrowFunc = lambda x: y0*x**Beta
            BorrowFunc = lambda x,y: y0BF*(x+y*AlphaBF)**BetaBF

            plotNoBorrow = []
            plotBorrow = []
            for a,b in zip(pop,aTraffic):
                plotBorrow.append(BorrowFunc(a,b))
                plotNoBorrow.append(noBorrowFunc(a))
            

            outDir = "Figures/BorrowedSizeModeling/"+years
            countryListName = ""
            if includeTag == 'ALL/COMBINED':
                countryListName = "AllCountriess"
            else:
                for country in countryList:
                    app = country + "-"
                    countryListName = countryListName + (app)
            outName = outDir + "/" + countryListName[:-1]+"_"+feat+ ".png"
            #outName = outDir + "/AllCountries_" + feat+ "_Connectivity"
            # TODO: Put Alphas on plots
            # TODO: Label lines
            plt.figure(outName)
            
            plt.loglog(pop,featVals, 'ro')
            x_space = pop# np.linspace(np.min(pop),np.max(pop),len(pop))
            plt.loglog(x_space, noBorrowFunc(x_space), ':k')
            plt.loglog(x_space, BorrowFunc(x_space,aTraffic), '--b')
            xLbl = "Population"
            yLbl = feat
            plt.xlabel(xLbl)
            plt.ylabel(yLbl)
            ttl = "Scaling with Borrowed Size Model"
            plt.title(ttl)

            plt.savefig(outName)
            plt.close()





            expectedFeatsStandard = []                
            expectedFeatsBorrow = []               


            for x,y in zip(pop,aTraffic):
                expectedFeatsStandard.append(noBorrowFunc(x))                
                expectedFeatsBorrow.append(BorrowFunc(x,y))                

            outName = outDir + "/" + countryListName[:-1]+"_"+feat+ "_ModelComparison"+ ".png"
            #outName = outDir + "/AllCountries_" + feat+ "_Connectivity"
            # TODO: Label lines
            plt.figure(outName)
            
            plt.loglog(featVals,expectedFeatsStandard, 'ro')
            plt.loglog(featVals,expectedFeatsBorrow, 'bo')
            plt.loglog(featVals,featVals, ':k')

        
            xLbl = "real Values"
            yLbl = "expected values (Red: Standard) (Blue: Borrowing)"
            plt.xlabel(xLbl)
            plt.ylabel(yLbl)
            ttl = "Borrowed Size Model vs. Standard Scaling Model"
            plt.title(ttl)

            plt.savefig(outName)
            plt.close()



            R2_NoBorrowed = sk.r2_score(featVals,expectedFeatsStandard)
            R2_WithBorrowed = sk.r2_score(featVals,expectedFeatsBorrow)

            aicNoBorrowed = aic.aic(featVals, expectedFeatsStandard, 2)
            aicWithBorrowed = aic.aic(featVals, expectedFeatsBorrow, 3)
            print("Standard: {}".format(aicNoBorrowed)," Borrowed: {}".format(aicWithBorrowed))


            #TODO: Fix [0]
            Alphas[countryList[0]] = 1/AlphaBF
            R2Ratios[countryList[0]] = R2_WithBorrowed/R2_NoBorrowed
            aicRatios[countryList[0]] = aicNoBorrowed/aicWithBorrowed



            #print("For Standard Scaling:\n, R^2 = {}, Beta = {}\n\nFor new model, \nR^2 = {}\nBeta={}\nAlpha={}\n\n".format(R2_NoBorrowed,Beta,R2_WithBorrowed,BetaBF,AlphaBF))
            
        print("Alphas: ")
        print(str(Alphas))
        print("R^2 Ratios: ", str(R2Ratios))
        print("AIC Ratios (>1 means improvement): ", str(aicRatios))

            

    
            
