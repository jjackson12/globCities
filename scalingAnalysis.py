import pandas as pd
import numpy as np
### This script is to run basic scaling law analyses





def scalingFunc(y_0,Beta):
    return lambda N: y_0*N**Beta