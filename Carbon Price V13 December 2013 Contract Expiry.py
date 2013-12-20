#Import libraries
import urllib2
from BeautifulSoup import BeautifulSoup
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
repo.git.pull() #maybe git fetch origin

#create soup
soup = BeautifulSoup(urllib2.urlopen('https://www.theice.com/marketdata/DelayedMarkets.shtml?productId=3418&hubId=4080').read())
table = soup.find('table', {"class":"data default borderless"})

#throw an error unless the right price is found
errorvar = "Vintage wasn't found"

#Find and record "last" price
price_idx = -1
for idx, th in enumerate(table.findAll('th')):
    # Find the column index of price
    if th.getText() == 'Last':
        price_idx = idx
        break

pricevar = 0
for tr in table.findAll('tr'):
    # Extract the content of each column in a list
    td_contents = [td.getText() for td in tr.findAll('td')]
    # If this row matches our requirement, take the Last column
    if 'Dec13' in td_contents:
        pricevar = td_contents[price_idx]
        errorvar = "no error"
        break


    


#Find and record time
time_idx = -1
for idx, th in enumerate(table.findAll('th')):
    # Find the column index of Time
    if th.getText() == 'Time':
        time_idx = idx
        break

timevar = []
for tr in table.findAll('tr'):
    # Extract the content of each column in a list
    td_contents = [td.getText() for td in tr.findAll('td')]
    # If this row matches our requirement, take the Time column
    if 'Dec13' in td_contents:
        time_str = td_contents[time_idx]
        # This will capture the date in the form: "Thu Dec 05 16:26:24 EST 2013 GMT", convert to datetime object
        time_obj = datetime.datetime.strptime(time_str,'%a %b %d %H:%M:%S EST %Y GMT')
        timevar.append(datetime.datetime.strftime(time_obj,'%m/%d/%Y'))

#if date was not found, print "1/1/1900" and record the error
if timevar == []:
    errorvar = "Vintage wasn't found"
    timevar = ['01/01/1900']



#Find and record volume traded
volume_idx = -1
for idx, th in enumerate(table.findAll('th')):
    # Find the column index of price
    if th.getText() == 'Volume':
        volume_idx = idx
        break

volvar = 0
for tr in table.findAll('tr'):
    # Extract the content of each column in a list
    td_contents = [td.getText() for td in tr.findAll('td')]
    # If this row matches our requirement, take the Last column
    if 'Dec13' in td_contents:
        volvar = td_contents[volume_idx]
        errorvar = "no error"
        break



#make sure we are in the right folder
os.chdir(repo_loc)

#create output document
f = open('carbon_prices_v13 contract dec 2013.csv','a')
f.write('\n')
f.write(timevar[0])
f.write(',')
f.write(str(pricevar))
f.close()

#Stage files for commit
repo.git.add('csv/carbon_prices_v13 contract dec 2013.csv')

#Commit the changes
repo.git.commit(m ='Latest carbon price update')

#Push the repo
#note: to automate login you must follow the instructions here: https://help.github.com/articles/set-up-git
repo.git.push()

#pull timestamp
pulltime = datetime.datetime.now()

#send email with success or failure
fromaddr = 'calcarbondash@gmail.com'
toaddrs = 'tucker.willsie@cpisf.org'
if errorvar == "no error":
    msg = "\r\n".join([
        "From: Calcarbondash@gmail.com",
        "To: Tucker.willsie@cpisf.org; dario@cpisf.org",
        "Subject: Status of upload",
        "",
        "Upload successful - todays upload was " +str(pricevar)+", "+str(timevar[0])+ ", "+str(volvar)+ ". The time of the pull was "+str(pulltime)
        ])
else:
    msg = "\r\n".join([
        "From: Calcarbondash@gmail.com",
        "To: Tucker.willsie@cpisf.org; dario@cpisf.org",
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
