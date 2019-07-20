import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as sk
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from RegscorePy import *
##### This script is to run basic scaling law analyses

### user configs
years = "2013-2016"
# input data file
fIn = "Features"+years.replace("-","_")+".xls"
#what features to analyze
#feats = ["GDP","Violent Crime","Total Robberies","Number of Visitors (Estimate by Accommodation GDP)"]
feats = ["GDP","Disposable Income per Household","Unemployment","Air Traffic"]
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
#'United Kingdom',
#'Italy',
#'United States (Census)'
]]


# set true if running on US census data
USData = False

# minimum number of datapoints to plot
dataPlotMin = 7
# what type of connectivity to use for residual plotting    
connectivityTags = {
    #"Connectivity (asymmetric)":1#,
    #"Connectivity (symmetric)":1#,
    #"Global Firm Presence (without Connectivity)":1.0
    "Air Traffic":1
}

# what to call this combination of connectivities in output file
connectivityLbl = "Air Traffic"
# Set true if you want to plot all possible countries individually#
#includeTag = 'ALL/SEPARATE' # this plots all countries on individual country plots
includeTag = 'ALL/COMBINED' # this plots all countries together
#includeTag = 'ALL/COMBINED+SEPARATE' # this plots each country individually plus all of EU as one (TODO: Not yet implemented)
#includeTag = 'LIST' # this allows manual lists of countries in "countries" above
# plot residuals vs connectivity
plotResiduals = False
# plot scaling relations
plotScaling = False
# try borrowed size fit with air traffic
borrowedSizeFit = True
# ratio of visitors per Accomodation GDP in USD (found from "extrapolateVisitors.py")
aGDP2visitors = 5091
# calculate residuals using difference ("diff") or ratio ("ratio") or "SAMI"
resCalc = "SAMI"
# name of external population measure used in borrowed size model testing
exPop = "Air Traffic"

# max size for point in plotting correlations
maxSize = 350












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









# NOTE: y0 is actually log(y0), which is what getScaleParams returns
# TODO: Fix this for later
def getResiduals(pop,feat,Beta,y0,featMean=1,manResCalc=resCalc):
    residuals = []
    for cityPop,cityFeat in zip(pop,feat):
        ## ratio
        if manResCalc=="ratio":
            residual = cityFeat/(np.exp(y0)*(cityPop**Beta))
        elif manResCalc=="diff":
            ## difference
            residual = cityFeat - (np.exp(y0)*(cityPop**Beta))
            # normalize by mean of that country's feature
            residual = residual/featMean
        elif manResCalc=="SAMI":
            logMean = np.average(np.log(feat))
            if logMean < 0 :
                logMean = logMean*-1
            residual = np.log(cityFeat/(np.exp(y0)*(cityPop**Beta)))/logMean
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
    


def getNetConnectivities(connData):
    finalConnectivities = np.zeros(len(connData.index))
    for connectivityTag in connectivityTags.keys():
        finalConnectivities = finalConnectivities + connectivityTags[connectivityTag] * np.array(connData[connectivityTag])
    # for considering connectivity as deviation from scaling expectation of connectivity
    BetaC,y0C = np.polyfit(np.log(connData["Population"]),np.log(finalConnectivities),1)
    return getResiduals(connData["Population"],finalConnectivities,BetaC,y0C,featMean=np.average(finalConnectivities),manResCalc="ratio")



if USData:
    allCountries = countries[0]

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

            #if not feat in linearFeats:
            #    x_pop = np.array(list(map(lambda x: np.log(x), x_pop)))
            #    y_feat = np.array(list(map(lambda x: np.log(x), y_feat)))


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

            if Beta>1:
                lbl = "Superlinear: Beta = "+str(round(Beta,3))
            elif Beta<1:
                lbl = "Sublinear: Beta = "+str(round(Beta,3))
            else:
                lbl = "Linear, Beta = 1"
            
            linFit = np.polyfit(plotData["Population"],plotData[feat],1)

            # plot scaling fitting

            if feat in linearFeats:
                plt.loglog(x_pop, y_feat, 'bo')
                x_space = np.linspace(np.min(x_pop),np.max(x_pop),len(x_pop))
                plt.loglog(x_space, Beta*x_space+y0, '--k',label=lbl)

            else:
                plt.loglog(x_pop, y_feat, 'bo')
                x_space = np.linspace(np.min(x_pop),np.max(x_pop),len(x_pop))
                plt.loglog(x_space, np.exp(y0)*x_space**Beta, '--k',label=lbl)

                # plot null hypothesis linear fit  FIXME
            plt.loglog(x_space, x_space*linFit[0]+linFit[1], ':r',label="Linear Fit") 
            



            # create name for plot
            countryListName = ""
            for country in countryList:
                app = country + ", "
                countryListName = countryListName + (app)
            plotName = feat + " scaling for " + countryListName

            # create labels, legends, etc
            plt.title(plotName)
            plt.legend()
            plt.xlabel('Population')
            yLab = feat
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
            residuals = {}
            connectivities = {}
            pops = {}
            allPops = []
            allResiduals = []
            allConnectivities = []
            countriesWithData = []
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
            
                countriesWithData.append(country)

                pops[country] = plotData["Population"]
                allPops = allPops + list(pops[country])

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

                residuals[country] = getResiduals(plotData["Population"],feats,Beta,y0,featMean=np.average(feats))

                

                newConnectivities = getNetConnectivities(plotData)

                    
                connectivities[country] = list(newConnectivities)#list(plotData[connectivityTag])
                
                allResiduals = allResiduals + list(residuals[country])
                allConnectivities = allConnectivities + list(connectivities[country])
        
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
            plt.figure(outName)
            # 
            #residuals = connScale(residuals)
            colors = {}
            maxPop = np.max(allPops)
            
            
            sizeCoeff = maxSize/maxPop
            minSize = sizeCoeff*np.min(allPops)
            cMap = plt.cm.get_cmap('hsv',len(countriesWithData)+1)
            i = 1
            # TODO: Label colors better (Hacky right now)
            for country in countriesWithData:
                first = True
                for c,r,p, in zip(connectivities[country],residuals[country],pops[country]):
                    size = p*sizeCoeff
                    if first:
                        plt.scatter(c,r,c=cMap(i),s=size)
                        plt.scatter(c,r,c=cMap(i),s=minSize,label=country)
                        first = False
                    else:
                        plt.scatter(c,r,c=cMap(i),s=size)
                i = i + 1  

            #loggedRes = list(map(lambda x: logVals))

            rVal,pVal = pearsonr(allConnectivities,allResiduals)
            pReport = "r={}\np = {}".format(rVal,pVal)
            print(pReport)
            plt.text(0.6,0.2,pReport,fontsize=12,transform=plt.gca().transAxes)
            xLbl = "deviation in " +connectivityLbl+" ("+resCalc+")"
            yLbl = "deviation in "+feat+" ("+resCalc+")"
            plt.xlabel(xLbl)
            plt.ylabel(yLbl)
            plt.legend()
            ttl = feat + " vs. "+connectivityLbl
            plt.title(ttl)
            #plt.gca().set_yscale("log")
            #plt.gca().set_xscale("log")

            plt.savefig(outName)
            plt.close()





def borrowedSizeModel(x,y0,Beta,Alpha):
    return y0*(x['pop']+x['aTraffic']*Alpha)**Beta

def borrowedSizeModelWithConns(x,y0,Beta,Alpha):
    return y0*(x['pop']+x['aTraffic']*x['conn']*Alpha)**Beta

def standardModel(x,y0,Beta):
    return y0*(x**Beta)


# Borrowed size fitting Analysis
if borrowedSizeFit:

    paramsList = ["n (Without Connectivity Data)","n (With Connectivity Data)","Beta (Standard Without Connectivity Data)","Beta (Borrowed Size)","Beta (Standard With Connectivity Data)","Beta (Borrowed Size With Connectivity)","Alpha (Borrowed Size)","Alpha (Borrowed Size With Connectivity)","BIC (Standard Without Connectivity Data)","BIC (Borrowed Size)","BIC (Standard With Connectivity Data)","BIC (Borrowed Size With Connectivity)","AIC (Standard Without Connectivity Data)","AIC (Borrowed Size)","AIC (Standard With Connectivity Data)","AIC (Borrowed Size With Connectivity)","R^2 (Standard Without Connectivity Data)","R^2 (Borrowed Size)","R^2 (Standard With Connectivity Data)","R^2 (Borrowed Size With Connectivity)"]
    retParams = {} 
    for useConns in [True,False]:
        useConnsInBorrow = useConns

        # do analysis seperately for every feature
        for feat in feats:
            if feat not in retParams.keys():
                retParams[feat] = pd.DataFrame(index=list(map(lambda x: x[0], countries)), columns=paramsList)

            # ignore connectivity vs connectivity
            skip = False
            for connectivityTag in connectivityTags.keys(): 
                if connectivityTag in feat:
                    skip = True
                    continue
            if skip:
                continue



            #FIXME: error with running all countries
            for countryList in countries:

                dataToPull = ["Population",feat,exPop]
                if useConnsInBorrow:
                    dataToPull = dataToPull + list(connectivityTags.keys())

                plotData = getDataFromList(countryList,dataToPull)

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
            
                #print("fitting for R^2 ",str(countryList))
                #print("feat, ",feat)

                pop = plotData["Population"]
                featVals = plotData[feat]
                aTraffic = plotData[exPop]
                if useConnsInBorrow:
                    conns = getNetConnectivities(plotData)

                #guess = ()
                # standard scaling parameters
                guess = (1,featVals[0]/pop[0])
                # FIXME: Fits are so off for some reason
                (y0,Beta), pcov = curve_fit(standardModel,pop,featVals,p0=guess)

                print(str((Beta,np.log(y0))))
                print(str(getScaleParams(plotData,feat)))

                (Beta,y0) = getScaleParams(plotData,feat)
                y0 = np.exp(y0)

                concatData = []

                if useConnsInBorrow:            
                    for a,b,c in zip(pop,aTraffic,conns):
                        concatData.append((a,b,c))
                        dtype = [('pop', float), ('aTraffic', float),('conn',float)]
                else:
                    for a,b in zip(pop,aTraffic):
                        concatData.append((a,b))
                        dtype = [('pop', float), ('aTraffic', float)]
                

                concatData = np.array(concatData,dtype=dtype)
                #concatData = np.sort(concatData, order='pop')
                #concatData = np.array(concatData)

                # y0, Beta, Alpha
                guess = (y0,Beta,0)
                # minimum alpha has to be such that N_i+Alpha*N_e is never zero or below
                alphaMin = -np.min(pop/aTraffic)*0.65
                if useConnsInBorrow:
                    params, pcov = curve_fit(borrowedSizeModelWithConns,concatData,featVals,guess,bounds=([y0/100,0.3,alphaMin],[y0*100,2,1.5]))
                else:
                    params, pcov = curve_fit(borrowedSizeModel,concatData,featVals,guess,bounds=([y0/100,0.3,alphaMin],[y0*100,2,1.5]))
                y0BF,BetaBF,AlphaBF = params


                noBorrowFunc = lambda x: y0*x**Beta
                BorrowFunc = lambda x,y: y0BF*(x+y*AlphaBF)**BetaBF
                BorrowConnFunc = lambda x,y,z: y0BF*(x+y*z*AlphaBF)**BetaBF

                plotNoBorrow = []
                plotBorrow = []
                if useConnsInBorrow:
                    for a,b,c in zip(pop,aTraffic,conns):
                        plotBorrow.append(BorrowConnFunc(a,b,c))
                        plotNoBorrow.append(noBorrowFunc(a))
                else:
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
                if useConnsInBorrow:
                    outName = outDir + "/" + countryListName[:-1]+"_"+feat+ "_WithConns.png"
                else:
                    outName = outDir + "/" + countryListName[:-1]+"_"+feat+ ".png"
                #outName = outDir + "/AllCountries_" + feat+ "_Connectivity"
                # TODO: Put Alphas on plots
                # TODO: Label lines
                plt.figure(outName)
                
                plt.loglog(pop,featVals, 'ro')
                x_space = pop# np.linspace(np.min(pop),np.max(pop),len(pop))
                plt.loglog(x_space, noBorrowFunc(x_space), ':k')
                if useConnsInBorrow:
                    plt.loglog(x_space, BorrowConnFunc(x_space,aTraffic,conns), 'bo')
                else:
                    plt.loglog(x_space, BorrowFunc(x_space,aTraffic), 'bo')
                xLbl = "Population"
                yLbl = feat
                plt.xlabel(xLbl)
                plt.ylabel(yLbl)
                ttl = "Scaling with Borrowed Size Model"
                plt.title(ttl)

                plt.savefig(outName)
                plt.close()






                if useConnsInBorrow:
                    outName = outDir + "/" + countryListName[:-1]+"_"+feat+ "_ModelComparisonWithConns"+ ".png"
                else:
                    outName = outDir + "/" + countryListName[:-1]+"_"+feat+ "_ModelComparison"+ ".png"
                #outName = outDir + "/AllCountries_" + feat+ "_Connectivity"
                # TODO: Label lines
                plt.figure(outName)
                
                plt.loglog(featVals,plotNoBorrow, 'ro')
                plt.loglog(featVals,plotBorrow, 'bo')
                plt.loglog(featVals,featVals, ':k')

            
                xLbl = "real Values"
                yLbl = "expected values (Red: Standard) (Blue: Borrowing)"
                plt.xlabel(xLbl)
                plt.ylabel(yLbl)
                ttl = "Borrowed Size Model vs. Standard Scaling Model"
                plt.title(ttl)

                plt.savefig(outName)
                plt.close()



                R2_NoBorrowed = sk.r2_score(featVals,plotNoBorrow)
                R2_WithBorrowed = sk.r2_score(featVals,plotBorrow)

                aicNoBorrowed = aic.aic(featVals, plotNoBorrow, 2)
                aicWithBorrowed = aic.aic(featVals, plotBorrow, 3)
                bicNoBorrowed = bic.bic(featVals, plotNoBorrow, 2)
                bicWithBorrowed = bic.bic(featVals, plotBorrow, 3)
                #print("Standard: {}".format(aicNoBorrowed)," Borrowed: {}".format(aicWithBorrowed))


                country = countryList[0]

                if useConnsInBorrow:
                    withConnData = "With"
                    connTag = " With Connectivity"
                else:
                    connTag = ""
                    withConnData = "Without"
                    
                alphaName = "Alpha (Borrowed Size"+connTag + ")"
                newR_2Name = "R^2 (Borrowed Size"+connTag + ")"
                newaicName = "AIC (Borrowed Size"+connTag+")"
                newbicName = "BIC (Borrowed Size"+connTag+")"
                newBetaName = "Beta (Borrowed Size"+connTag+")"


                standardR_2Name = "R^2 (Standard "+withConnData+" Connectivity Data)"
                standardbicName = "BIC (Standard "+withConnData+" Connectivity Data)"
                standardaicName = "AIC (Standard "+withConnData+" Connectivity Data)"
                standardBetaName = "Beta (Standard "+withConnData+" Connectivity Data)"



                retParams[feat][alphaName][country] = 1/AlphaBF
                retParams[feat][newR_2Name][country] = R2_WithBorrowed
                retParams[feat][newaicName][country] = aicWithBorrowed
                retParams[feat][newbicName][country] = bicWithBorrowed
                retParams[feat][newBetaName][country] = BetaBF

                retParams[feat][standardR_2Name][country] = R2_NoBorrowed
                retParams[feat][standardaicName][country] = aicNoBorrowed
                retParams[feat][standardbicName][country] = bicNoBorrowed
                retParams[feat][standardBetaName][country] = Beta
                
                retParams[feat]["n ("+withConnData + " Connectivity Data)"][country] = len(pop)

        #print(feat)
        #print(str(retParams))

            #print("For Standard Scaling:\n, R^2 = {}, Beta = {}\n\nFor new model, \nR^2 = {}\nBeta={}\nAlpha={}\n\n".format(R2_NoBorrowed,Beta,R2_WithBorrowed,BetaBF,AlphaBF))
            
    #TODO: Output a table image
    #print(str(retParams))
    with pd.ExcelWriter("Figures/BorrowedSizeModeling/fitParameters.xls") as writer:
        for feat in feats:
            if feat in retParams.keys():
                retParams[feat].dropna(how='all').to_excel(writer,sheet_name=feat)

            

    
            
