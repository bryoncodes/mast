#!/usr/bin/env python
'''
MAST Group 1 - Bryon Burleigh, Freelin Hummel, Kabir Kang

Receives email body piped from procmail:

    Advising Signup with <advisor> <confirmed|CANCELLED>
    Name: <name>
    Email: <student email address>
    Date: <Day>, <Month><date><st|nd|rd|th>, <year>
    Time: 1:00pm - 1:15pm

Creates new email with attachment MIMETYPE "text/calendar; method=<REQUEST|CANCEL>;"



This will successfully send an email via engr servers, but only if it is run 
ON an engr server. For example, you should not be able to successfuly run 
this script locally.

Big thanks to Masahide Kanzaki who took RFC 2445 and made it accessible to humans
at his site.
http://www.kanzaki.com/docs/ical/

Also Wikipedia http://en.wikipedia.org/wiki/ICalendar

Additional thanks to the maintainers of Python documentation. 
https://docs.python.org/2/library/email-examples.html 


'''


import smtplib
import time
import socket
import fileinput
import string
import re
from os.path import expanduser
from pprint import pformat
from pprint import pprint
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import database

debugs = False
home = expanduser("~")


# Read email body piped from procmail
mailArray = []
for line in fileinput.input():
	mailArray.append(line.split())

body=[]

if (len(mailArray[0])==0):
    mailArray[0].append("\n") # some lines are read in as blank, and need a "\n" instead of null

for i in range(0, len(mailArray)):
    if i == len(mailArray)-1:
        break

    if (len(mailArray[i+1])==0):
        mailArray[i+1].append("\n") # some lines are read in as blank, and need a "\n" instead of null

    if mailArray[i][0].lower() == "advising":
        bodyStart = i
    
for i in range(bodyStart, len(mailArray)):
    # build 2d array of relevant parts of email body
    if (mailArray[i][0].lower()=="please"):
        body.append(mailArray[i])
        break
    else:
        body.append(mailArray[i])

# Get student info for database
studentName = studentEmail = ""
for i in range(1,len(body[1])):
    studentName+=body[1][i]
    if i<len(body[1])-1:
        studentName+=" "

studentEmail=body[2][-1]

# Get email address from .mastrc
f = open(home+"/.mastrc", "r")
advisor_info = f.readline().split()
f.close()
advisorEmail = advisor_info[0]

# me == sender's email address (Do Not Reply)
# you == advisor's email address(es)
me = "do.not.reply@oregonstate.edu"
you = advisorEmail


# Start building attributes for calendar request object
timecreated = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())

# Build the DTSTART and DTEND time objects
body[3][3]=re.sub(r'[a-z]', "", body[3][3])
date = " ".join(body[3][1:])
date=date.replace(",","")
dateStart = dateEnd = date

# DTSTART   
ampm=re.sub(r'[0-9]*:[0-9]*', '', body[4][1])
aptStartHr = re.sub(r':[0-9]*[A-z]*', '', body[4][1])
aptStartMin  = re.sub(r'[0-9]*:', '', body[4][1])
aptStartMin = re.sub(r'[A-z]*', '', aptStartMin)

if ampm.lower() == "pm":
    aptStartHr = str(int(aptStartHr) + 12)

dateStart+=" "+aptStartHr+" "+aptStartMin+" 00"
timestart = time.strftime('%Y%m%dT%H%M%S', time.strptime(dateStart, '%A %B %d %Y %H %M %S'))
dbDate = time.strftime('%A, %B %d, %Y', time.strptime(dateStart, '%A %B %d %Y %H %M %S'))
dbTime = body[4][1]+" - "+body[4][3]

# DTEND   
ampm=re.sub(r'[0-9]*:[0-9]*', '', body[4][3])
aptEndHr = re.sub(r':[0-9]*[A-z]*', '', body[4][3])
aptEndMin  = re.sub(r'[0-9]*:', '', body[4][3])
aptEndMin = re.sub(r'[A-z]*', '', aptEndMin)

if ampm.lower() == "pm":
    aptEndHr = str(int(aptEndHr) + 12)

dateEnd+=" "+aptEndHr+" "+aptEndMin+" 00"
timeend = time.strftime('%Y%m%dT%H%M%S', time.strptime(dateEnd, '%A %B %d %Y %H %M %S'))

# Build unique appointment identifier based on advisor and appointment start & end times
# This needs to be globally unique. In theory no advisor will be double-booked, so this
# should have no problem being a unique value
uid = timestart+timeend+advisorEmail+studentEmail

# Determine whether appointment is confirmed or cancelled
if body[0][-1].lower() == "confirmed":
    calMethod="REQUEST"
    calStatus="CONFIRMED"
    cancelled = False
    subject = "New Advising Session"
else:
    calMethod="CANCEL"
    calStatus="CANCELLED"
    cancelled = True
    subject = "Advising Session Cancelled"

# Create message container - the correct MIME type is multipart/alternative (maybe? it works, anyways)  
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = me
msg['To'] = you

# Create the body of the message for the email, as well as the description in the calendar request
mimeText = ""
calText = ""
for x in body:
	mimeText += " ".join(x) + "\n"
	calText += " ".join(x) + "\\n" #Description of calReq needs escaped \n

'''
Below is the calendar request object

The following date-time attributes must be UTC:
    CREATED
    DTSTAMP
    LAST-MODIFIED

The UID attribute must be globally unique in the calendar system
'''

calReq = """\
BEGIN:VCALENDAR
METHOD:%s
PRODID:MAST
VERSION:2.0
BEGIN:VEVENT
CREATED:%s
DTSTAMP:%s
DTSTART:%s
DTEND:%s
LAST-MODIFIED:%s
SUMMARY:EECS Advising Session
UID:%s
DESCRIPTION:%s
SEQUENCE:0
STATUS:%s
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR
""" % (calMethod, timecreated, timecreated, timestart, timeend, timecreated, uid, calText, calStatus)


# Record the MIME types of both parts - text/plain and text/calendar.
part1 = MIMEText(mimeText, 'plain')
part2 = MIMEText(calReq, 'calendar')
part2.add_header('Content-Disposition', 'attachment', method=calMethod)

# Attach parts into message container.
msg.attach(part1)
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP('mail.engr.oregonstate.edu')
s.sendmail(me, you, msg.as_string())
s.quit()

# Add/Delete appointment to database
if cancelled:
    database.delete_appointment(uid)
else:
    database.add_appointment(advisorEmail, studentName, studentEmail, dbDate, dbTime, uid) 


# Debugging stuff
if (debugs):
    f=open(home+"/output.txt", "w")
    f.write(pformat(body))
    f.write("\n")
    f.write(pformat(advisorEmail))
    f.write("\n")
    f.write(pformat(mailArray))
    f.write("\n\n BODY:\n")
    f.write(pformat(body)+"\n")
    f.write(calReq)
    f.close()


