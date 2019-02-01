# Workflow

* #### Download template files
The first step is to download the Google Sheet file as a *csv file into the $OPERATIONS/TEMPLATE and generate the *template files (done by `generate_templates.py`).

* #### Check for new SAR acquisitions
The second step is to check whetehr there are new acquisitions available for a dataset. The `stored_date.date` file located in the `$OPERATIONS` directory contains the information on the last processed image for each dataset 

'''
GalapagosSenDT128: 2018-12-22T11:49:42.000000
GalapagosSenAT106: 2018-11-27T00:26:02.000000
KilaueaSenD87: 2018-12-01T16:16:11.000000
KilaueaSenAT124: 2018-11-10T04:30:34.000000```
'''

# Logging
The following information from each run is copied to the $OPERATIONS/LOGS directory:
* Does not need 

# How to monitor whether everything is working?
You can check ...


# Planned changes
 
Several items of the workflow  work fine but are not very efficient. The following will be improved in the future:

* Does not need to do every day....
* Some data sets do need to be updated once a month...
