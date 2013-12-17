#Import libraries
import urllib2
from bs4 import BeautifulSoup
import datetime
import smtplib
import git
import os

#create var that will track errors
errorvar = "no error"

#Define repo location & url locations
repo = git.Repo('/users/CPIGuest/Documents/GitHub/dashboard')
url = "https://github.com/climatepolicy/dashboard"
repo_loc = '/users/CPIGuest/Documents/GitHub/dashboard/csv'

#Update repo
repo.git.reset()
repo.git.checkout() #maybe git fetch origin

#create soup
soup = BeautifulSoup(urllib2.urlopen('https://www.theice.com/marketdata/DelayedMarkets.shtml?productId=3418&hubId=4080').read())
table = soup.find('table', {"class":"data default borderless"})

#throw an error unless the right price is found
errorvar = "Vintage wasn't found"

#Find and record "last" price
price_idx = -1
for idx, th in enumerate(table.find_all('th')):
    # Find the column index of price
    if th.get_text() == 'Last':
        price_idx = idx
        break

pricevar = 0
for tr in table.find_all('tr'):
    # Extract the content of each column in a list
    td_contents = [td.get_text() for td in tr.find_all('td')]
    # If this row matches our requirement, take the Last column
    if 'Dec13' in td_contents:
        pricevar = td_contents[price_idx]
        errorvar = "no error"
        break


    


#Find and record time
time_idx = -1
for idx, th in enumerate(table.find_all('th')):
    # Find the column index of Time
    if th.get_text() == 'Time':
        time_idx = idx
        break

timevar = []
for tr in table.find_all('tr'):
    # Extract the content of each column in a list
    td_contents = [td.get_text() for td in tr.find_all('td')]
    # If this row matches our requirement, take the Time column
    if 'Dec13' in td_contents:
        time_str = td_contents[time_idx]
        # This will capture the date in the form: "Thu Dec 05 16:26:24 EST 2013 GMT", convert to datetime object
        time_obj = datetime.datetime.strptime(time_str,'%a %b %d %H:%M:%S EST %Y GMT')
        timevar.append(datetime.datetime.strftime(time_obj,'%x'))

#if date was not found, print "1/1/1900" and record the error
if timevar == []:
    errorvar = "Vintage wasn't found"
    timevar = ['01/01/1900']

#make sure we are in the right folder
os.chdir(repo_loc)

#create output document
f = open('carbon_prices_test.csv','a')
f.write(timevar[0])
f.write(',')
f.write(str(pricevar))
f.write('\n')
f.close()

#pull timestamp
pulltime = datetime.datetime.now()

#send email with success or failure
fromaddr = 'calcarbondash@gmail.com'
toaddrs = 'tucker.willsie@cpisf.org'
if errorvar == "no error":
    msg = "\r\n".join([
        "From: Calcarbondash@gmail.com",
        "To: Tucker.willsie@cpisf.org",
        "Subject: Status of upload",
        "",
        "Upload successful - todays upload was " +str(pricevar)+", "+str(timevar[0])+ ". The time of the pull was "+str(pulltime)
        ])
else:
    msg = "\r\n".join([
        "From: Calcarbondash@gmail.com",
        "To: Tucker.willsie@cpisf.org",
        "Subject: Status of upload",
        "",
        "Upload error - The time of the pull was "+str(pulltime)+" and the error was: "+errorvar
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

#Stage files for commit
repo.git.add('carbon_prices_test.csv')

#Commit the changes
repo.git.commit(m ='Latest carbon price update')

#Push the repo
#note: to automate login you must follow the instructions here: https://help.github.com/articles/set-up-git
repo.git.push()
