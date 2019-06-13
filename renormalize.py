# filenames of data containing city properties for cities in US and UK
fIn_US = ""
fIn_UK = ""
# filename for output renormaliked data
fOut = "renorm_USUK.csv"


# list of properties being analyzed in each city
propNames = ["crime","GDP"]

# map: propName -> array[city|population|propVal]
propData_US = readData(fIn_US)
propData_UK = readData(fIn_UK)

# map: propName -> renormParameter[Float]
# the renormParameter is defined as x such that x*Y_0(UK) = Y_0(US)
renormParam = {}

# for every property specified in "propNames":
#   1) Plot both US and UK log-log plots, and for each, extract
#      Beta and y_0 
#   2) Collect renormalization parameters
foreach propName in propNames:

    #   1) Plot both US and UK log-log plots, and for each, extract
    #      Beta and y_0 

    # These are simply arrays containing Beta in index 0 and y_0
    # in index 1
    US_fit = getFitParams(propData_US)
    UK_fit = getFitParams(propData_UK)

    # check values. If Beta is very different across the two, that may be a concern!
    # TODO: Are Betas different?
    print("Beta of US: ",US_fit[0],"Beta of UK: ",UK_fit[0])
    print("Y_0 of US: ",US_fit[1],"Y_0 of UK: ",UK_fit[1])


    #    2) Collect renormalization parameters
    # renormalization paramater is created so as to multiply to the UK value
    # to normalize it to the US value
    renormParam[propName] = US_fit[1]/US_fit[0]

# delete file if it exists
# Create output file
# Open to write
openOutFile()
# counter for iterating over data columns
i = 0

# rewrite normalized data to output file
foreach propName in propNames:
    # on the first run, write in columns index 0 and 1, the city names and 
    # populations, respectively, of BOTH US and UK cities together
    if(i=0): writeCities()
    
    # for every city in UK, write in the renormalized data
    foreach cityData in propData_UK[propName]:
        # write the renormalized data
        writeIn(cityData[0],cityData[2]*renormParam[propName],i)
    
    # for every city in US, write in the renormalized data
    foreach cityData in propData_US[propName]:
        # write the renormalized data
        writeIn(cityData[0],cityData[2],i)
    
    #increment counter
    i++

# save and close output Datafile
closeOutput

#input: string of datafile
#output: map: propName -> array[city|population|propVal]
def readData(dFile):
    return []

#input: map: propName -> array[city|population|propVal]
#output: array with Beta in index 0 and y_0 in index 1
def getFitParams(dataMap):
    # TODO: Plot fits
    return []

# write the renormalized data into the output file
def writeIn(city,dVal,colIndex):
