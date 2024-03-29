import curses
import sys
import random
import time
import database
import MySQLdb
import smtplib
from email.mime.text import MIMEText
"""
Group 1 MAST - Kabir Kang, Bryon Burleigh, Freelin Hummel
CS 419
This Python file defines a Curses screen that is scrollable. It accepts keyboard input d for deleting entries and q for quitting. If deletion is selected on an appointment, a cancellation email is generated that will be intercepted by .procmailrc.

Here is the curses client main interface class
This interface uses modified code from https://github.com/LyleScott/Python-curses-Scrolling-Example/blob/master/curses_scrolling.py for the scrolling portion of the interface.

"""


class AppointmentsInterface:
    DOWN = 1
    UP = -1

    appointment_lines = []
    screen = None
    # Description: This function initializes a screen that we can affect with curses        
    def __init__(self, advisor_email, advisor_name):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.advisor_email = advisor_email
        self.advisor_name = advisor_name
        self.screen.keypad(1) 
        self.screen.border(0)
        self.top_line = 0
        self.selected_line = 0
        self.get_appointment_lines()
        self.run()

# Description: This logic listens for keyboard input in the CLI. Keying up or down will change the selected appointment. D deletes an appointment, and Q quits
   
    def run(self):
        while True:
            #continually update screen
            self.display_screen()
            #respond to pressed keys
            c = self.screen.getch()
            if c == curses.KEY_UP: 
                self.updown(self.UP)
            elif c == curses.KEY_DOWN:
                self.updown(self.DOWN)
            elif c == ord('d'):
                self.cancel_email()
            elif c == ord('q'):
                self.restore_screen()
                break

    def cancel_email(self):
        apt_num = self.top_line + self.selected_line
        appointments = database.get_appointments(self.advisor_email)
        apt_to_cancel = appointments[apt_num]

        student_name = str(apt_to_cancel[1])
        student_email = apt_to_cancel[2]
        date = apt_to_cancel[3]
        time = apt_to_cancel[4]
        message_text = ""

        me = "do.not.reply@engr.orst.edu"
        you = self.advisor_email

        msg_text = '''
Advising Signup with %s CANCELLED 
Name: %s
Email: %s
Date: %s
Time: %s
Please contact support@engr.oregonstate.edu if you experience problems

''' % (self.advisor_name, student_name, student_email, date, time)

        msg = MIMEText(msg_text)
        msg['Subject'] = 'Advising Signup Cancellation'
        msg['From'] = me
        msg['To'] = you

        s = smtplib.SMTP('mail.engr.oregonstate.edu')
        s.sendmail(me, you, msg.as_string())
        s.quit()
        del self.appointment_lines[apt_num]
        self.num_appointments = len(self.appointment_lines)

    def get_appointment_lines(self):
        #retrieve appointments from database and add them to the lines to display
        appointments = database.get_appointments(self.advisor_email)
        self.appointment_lines = []
        for apt in appointments:
            aptDate = time.strftime('%m-%d-%Y', time.strptime(apt[3], '%A, %B %d, %Y'))
            appt = '%s\t%s\t%s' % (apt[1],aptDate,apt[4])
            self.appointment_lines.append(appt)

        #if appointment_lines == []:
         #   self.appointment_lines.append("No Appointments!")

        self.num_appointments = len(self.appointment_lines)
        

    def display_screen(self):
        self.screen.erase()
        top = self.top_line
        bottom = self.top_line+curses.LINES
        self.screen.addstr(0,0, "No Appointments")
        for (index,line) in enumerate(self.appointment_lines[top:bottom]):
            linenum = self.top_line + index

            line = '%s' % (line)
          
            if index != self.selected_line:
                self.screen.addstr(index, 0, line)
            else:
                self.screen.addstr(index, 0, line, curses.A_STANDOUT)

        self.screen.addstr(0,50,"d->delete  q->quit",curses.A_BOLD)
        self.screen.refresh()

    def updown(self, increment):
        next_line = self.selected_line + increment

        #if at the top of the screen and the line above current line is not the first element of the list, change view to show next line
        if increment == self.UP and self.selected_line == 0 and self.top_line != 0:
            self.top_line += self.UP 
            return
        #if at the bottom of the screen and if the line below current line is not the last element, move down, change view to show next line
        elif increment == self.DOWN and next_line == curses.LINES and (self.top_line+curses.LINES) != self.num_appointments:
            self.top_line += self.DOWN
            return

        #if selected line is not at the top, move up
        if increment == self.UP and (self.top_line != 0 or self.selected_line != 0):
            self.selected_line = next_line
        #if selected line is not at the bottom, move down
        elif increment == self.DOWN and (self.top_line+self.selected_line+1) != self.num_appointments and self.selected_line != curses.LINES:
            self.selected_line = next_line

 
    def restore_screen(self):
        curses.initscr()
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    
    def __del__(self):
        #if terminated, end curses so the terminal stays intact
        self.restore_screen()
