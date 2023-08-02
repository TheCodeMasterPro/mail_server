##########################################
# This file is for testing purposes only #
##########################################
import smtplib
import email.utils
from email.mime.text import MIMEText
import poplib
import datetime

def send_email():
    # Create the message
    msg = MIMEText('This is the body of the message.\nAnother test\nAnd another')
    msg['To'] = email.utils.formataddr(('test', 'user1@blabla.com'))
    msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
    msg['Subject'] = 'Simple test message'
    msg['Date'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    print(msg)

    server = smtplib.SMTP('127.0.0.1', 25)
    server.set_debuglevel(True) # show communication with the server
    try:
        server.sendmail('author@example.com', ['user1@blabla.com'], msg.as_string())
    finally:
        server.quit()

def retrieve_emails():
    M = poplib.POP3('localhost')
    M.set_debuglevel(2)
    M.user("yoav")
    M.pass_("12345")
    numMessages = len(M.list()[1])
    for i in range(numMessages):
        for j in M.retr(i+1)[1]:
            print(j)
    M.top(1, 4)
    M.quit()

def main():
    send_email()
    retrieve_emails()

if __name__ == '__main__':
    main()