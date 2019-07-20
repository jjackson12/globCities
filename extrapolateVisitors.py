import pandas as pd
import copy
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
import numpy as np
import re
### This script extrapolates number of visitors to US cities based on travel-related GDP



dIn = pd.read_excel("FeaturesUS2013_2016.xls",sheet_name="United States").set_index("City")


dAccomRatios = dIn[["Accommodation GDP","Number of Visitors"]].dropna()

aGDP = dAccomRatios["Accommodation GDP"]
nVisit = dAccomRatios["Number of Visitors"]

plt.figure()

(m),pcov = curve_fit(lambda x,m: m*x, dAccomRatios["Accommodation GDP"],dAccomRatios["Number of Visitors"])
x_space = np.linspace(np.min(aGDP),np.max(aGDP),len(aGDP))
print(m)
plt.plot(x_space,m*x_space,"k:")
plt.plot(dAccomRatios["Accommodation GDP"],dAccomRatios["Number of Visitors"],'bo')
plt.show()
plt.close()
