#--------------------------------------------------------------------------------
# Step 1: Set up initial variables and libraries
#--------------------------------------------------------------------------------

#Import libraries
import urllib2
from BeautifulSoup import BeautifulSoup
import datetime
import smtplib
import git
import os
import csv
from os.path import exists

#create var that will track errors
errorlist = []

#temporarily create list of contract dates. Eventually this should probably be generated dynamically
#or at least in a csv file that is read in the script
contract_dates = ['Dec14','Jan14']
#,'Feb14','Mar14','Apr14','May14','Jun14','Jul14','Aug14'

#Define repo location & url locations
repo = git.Repo('/users/CPIGuest/Documents/GitHub/dashboard')
url = "https://github.com/climatepolicy/dashboard"
repo_loc = '/users/CPIGuest/Documents/GitHub/dashboard/csv'

#Update repo
repo.git.reset()
repo.git.pull() #maybe git fetch origin
            
#create soup
soup = BeautifulSoup(urllib2.urlopen('https://www.theice.com/marketdata/DelayedMarkets.shtml?productId=3418&hubId=4080').read())
table = soup.find('table', {"class":"data default borderless"})

#pull the "last update time" from the ICE website and convert it to PST (-8 hours)
lastupdatetime = soup.find('div', {"class":"updateTime"})
lastupdatetimetext = lastupdatetime.getText()
lastupdatetime_obj = datetime.datetime.strptime(lastupdatetimetext,'Last update time:&nbsp;%a %b %d %H:%M:%S EST %Y GMT')
lastupdatetime_timezone_correction_obj = lastupdatetime_obj-datetime.timedelta(hours=8)
lastupdatevar = datetime.datetime.strftime(lastupdatetime_timezone_correction_obj,'%m/%d/%Y')

#--------------------------------------------------------
#loop begins
#--------------------------------------------------------
for contract_date in contract_dates:
    # coding the creation of new CSVs for any contract periods that don't already exist
#    if exists('carbon_prices_v13 contract '+str(contract_date)+'.csv'):
#        donothing = 'ok'
#    else:
#        f = open('carbon_prices_v13 contract '+str(contract_date)+'.csv','a')
#        f.write('date,close,volume')
#        f.close

#Read the last row already on the chart so that we can check to see if the ICE website has updated data
#and we can use the previous price if there is zero trading volume today
    with open('/Users/cpiguest/Documents/GitHub/dashboard/csv/carbon_prices_v13 contract '+str(contract_date)+'.csv','r') as f:
        reader = csv.reader(f)
        lastline = reader.next()
        for line in reader:
            lastline = line
            
#--------------------------------------------------------------------------------
# Step 2: Identify correct columns in table and error check that they all exist
#--------------------------------------------------------------------------------

#Find and record contract, time, price, and volume column locations (i.e. indexes)
    price_idx = -1
    volume_idx = -1
    time_idx = -1
    for idx, th in enumerate(table.findAll('th')):
    # Find the column index of Time
        if th.getText() == 'Last':
            price_idx = idx
        elif th.getText() == 'Volume':
            volume_idx = idx
        elif th.getText() == 'Time':
            time_idx = idx

# this defines the errors in case the script is unable to find the price, volume, or time columns within the table (which it will later use as reference points)
    if price_idx == -1:
        errorlist.append('Last (price) column not found')
    ##jump to email function
    if volume_idx == -1:
        errorlist.append('Volume column not found')
    ##jump to email function
    if time_idx == -1:
        errorlist.append('Time column not found')
    ##jump to email function

#--------------------------------------------------------------------------------
# Step 3: Iterate through all contract dates and pull price, volume and time for each contract
#--------------------------------------------------------------------------------

#Find and record "last" price, volume, and time
    pricevar = 0
    volvar = '0'
    timevar = ''
    for tablerow in table.findAll('tr'):
    # Extract the content of each column in a list
        td_contents = [cell.getText() for cell in tablerow.findAll('td')]
        # If this row matches our requirement, take the Last column
        if contract_date in td_contents:
            pricevar = td_contents[price_idx]
            volvar = td_contents[volume_idx]
            time_str = td_contents[time_idx]
            if time_str != 'GMT':    
                # This will capture the date in the form: "Thu Dec 05 16:26:24 EST 2013 GMT", convert to datetime object and convert from GMT to PST
                time_obj = datetime.datetime.strptime(time_str,'%a %b %d %H:%M:%S EST %Y GMT')
                time_timezone_correction_obj = time_obj-datetime.timedelta(hours=8)
                timevar = datetime.datetime.strftime(time_timezone_correction_obj,'%m/%d/%Y') 
            else:    
                # This will capture instances when the timestamp is not in our desired format
                errorlist.append("Invalid timestamp format")
                timevar = '01/01/1900'

    if volvar == '0':
        # conditional for taking the previous day's information if volume is zero - pricevar and volvar are based on CSV columns
        pricevar = lastline[1]
        timevar = lastupdatevar

#--------------------------------------------------------------------------------
# Step 4-success: If values pass error checks, write them to file
#--------------------------------------------------------------------------------

    #create output document
    os.chdir(repo_loc) #make sure we are in the right folder
    f = open('carbon_prices_v13 contract '+str(contract_date)+'.csv','a')
    f.write('\n')
    f.write(str(timevar))
    f.write(',')
    f.write(str(pricevar))
    f.write(',')
    f.write(str(volvar))
    f.close()

    #Stage files for commit
    repo.git.add('csv/carbon_prices_v13 contract '+str(contract_date)+'.csv')
    
#--------------------------------------------------------------------------------
# Step 5: Commit changes to repo and write summary email with news of success or failure
#--------------------------------------------------------------------------------

#Commit the changes
repo.git.commit(m ='Latest carbon price update')

#Push the repo
#note: to automate login you must follow the instructions here: https://help.github.com/articles/set-up-git
repo.git.push()

#pull timestamp
pulltime = datetime.datetime.now()

#convert error list into string
errorstring = ''
for error_idx in range(len(errorlist)):
    errorstring = errorstring + '\n' + str(errorlist[error_idx])

#send email with success or failure
fromaddr = 'calcarbondash@gmail.com'
toaddrs = 'tucker.willsie@cpisf.org'
if errorlist == []:
    msg = "\r\n".join([
    "From: Calcarbondash@gmail.com",
    "To: Tucker.willsie@cpisf.org; dario@cpisf.org",
    "Subject: Status of upload V13 Dec 14",
    "",
    "Upload successful - todays upload was " +str(pricevar)+", "+str(timevar[0])+ ", "+str(volvar)+ ". The time of the pull was "+str(pulltime)
    ])
else:
    msg = "\r\n".join([
    "From: Calcarbondash@gmail.com",
    "To: Tucker.willsie@cpisf.org; dario@cpisf.org",
    "Subject: Status of upload V13 Dec 14",
    "",
    "Upload error - The time of the pull was "+str(pulltime)+" and the error was: "+errorstring
    ])

#credentials
username = 'CalCarbonDash'
password = 'CalCarbon123'

# Send the message via SMTP server, but don't include the envelope header.
server = smtplib.SMTP(host='smtp.gmail.com', port=587)
server.starttls()
server.login(username,password)
server.sendmail(fromaddr, toaddrs, msg)
server.quit()




