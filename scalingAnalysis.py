import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
##### This script is to run basic scaling law analyses

### user configs
# input data file
fIn = "EUFeatures.xls"
#what features to analyze
feats = ["GDP","Patents"]
# what countries to analyze
countries = ["United Kingdom","Germany","Spain","France","Netherlands","Italy","Poland","Romania"]

#map, mapping countryname to dataframe
data = {}
#TODO: Allow for combining multiple country data
for country in countries:
    data[country] = pd.read_excel(fIn,sheet_name=country)
    for feat in feats:
        plotData = data[country][["Population",feat]].dropna()
        #extract Population as x-axis and the feature you're analyzing as the y-axes, such as GDP
        x_pop = plotData["Population"]
        y_feat = plotData[feat]
        # transform to log-log space
        x_pop = np.array(list(map(lambda x: np.log(x), x_pop)))
        y_feat = np.array(list(map(lambda x: np.log(x), y_feat)))
        # fit to linear function, extract Beta and y_0
        Beta,y0 = np.polyfit(x_pop, y_feat, 1) 
        x_space = np.linspace(np.min(x_pop),np.max(x_pop),len(x_pop))
        plt.figure()
        plt.plot(x_pop, y_feat, 'bo')
        if Beta>1:
            lbl = "Superlinear: Beta = "+str(round(Beta,3))
        elif Beta<1:
            lbl = "Sublinear: Beta = "+str(round(Beta,3))
        else:
            lbl = "Linear, Beta = 1"
        plt.plot(x_space, Beta*x_space+y0, '--k',label=lbl)
        plt.plot(x_space, x_space + np.min(x_pop)*Beta + y0 -np.min(x_pop), ':r',label="Linear Fit") 
        #plt.show() 
        plotName = feat + " scaling for "+country
        plt.title(plotName)
        plt.legend()
        plt.xlabel('Population')
        plt.ylabel(feat)
        #save to file
        outName = country+"_"+feat+".png"
        plt.savefig(outName)


