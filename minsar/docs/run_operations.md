# Workflow

* #### Download template files
The first step is to download the Google Sheet file as a *.csv file into the $OPERATIONS/TEMPLATE and generate the *template files (done by `generate_templates.py`). Manipulation of the `test_sheet` variable allows for the user to specify a secondary, non-production, google sheet to use. Simply gather the sheet id from the google sheet URL (see below) and set `test_sheet=sheet_id` 

For the below google sheet:

https://docs.google.com/spreadsheets/d/1zAsa5cykv-WSq1uf4CZdvFvaOer3Akol8aqbANnsd3E/edit#

the `sheet_id` is `1zAsa5cykv-WSq1uf4CZdvFvaOer3Akol8aqbANnsd3E`. 


* #### Check for new SAR acquisitions
The second step is to check whether there are new acquisitions available for a dataset. The `stored_date.date` file located in the `$OPERATIONS` directory contains the information on the last processed image for each dataset 

'''
GalapagosSenDT128: 2018-12-22T11:49:42.000000<br />
GalapagosSenAT106: 2018-11-27T00:26:02.000000<br />
KilaueaSenD87: 2018-12-01T16:16:11.000000<br />
KilaueaSenAT124: 2018-11-10T04:30:34.000000

It is highly discouraged to edit the `stored_date.date` file manually, as the datetime format is explicitly required for proper comparsions to be run. If you must edit the `stored_date.date` file do so carefully so as not to disturb the datetime format. The format is as follows: `yyyy-MM-ddThh:mm:ss`.

# Logging
The following information from each run is copied to the $OPERATIONS/LOGS directory:
* Does not need 

# How to monitor whether everything is working?
You can check ...


# Planned changes
 
Several items of the workflow  work fine but are not very efficient. The following will be improved in the future:

* Does not need to do every day....
* Some data sets do need to be updated once a month...
