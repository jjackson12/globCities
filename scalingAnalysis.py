import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
##### This script is to run basic scaling law analyses

### user configs
# input data file
fIn = "EUFeatures.xls"
#what features to analyze
feats = ["GDP","Patents"]


data = pd.read_excel(fIn)
data.set_index('METROREG/TIME')
data = data.dropna()
for feat in feats:
    #extract Population as x-axis and the feature you're analyzing as the y-axes, such as GDP
    #TODO: Is this the right datatype?
    x_pop = data["Population"]
    y_feat = data[feat]
    # transform to log-log space
    x_pop = np.array(list(map(lambda x: np.log(x), x_pop)))
    y_feat = np.array(list(map(lambda x: np.log(x), y_feat)))
    # fit to linear function, extract Beta and y_0
    Beta,y0 = np.polyfit(x_pop, y_feat, 1) 
    # plot TODO and save, and label, and display Beta value
    plt.plot(x_pop, y_feat, 'yo', x_pop, Beta*x_pop+y0, '--k') 
    plt.show() 


    



def scalingFunc(y_0,Beta):
    return lambda N: y_0*N**Beta