from threading import Thread
import popserver
import smtpserver
import database

def main():
    database.initiate()
    Thread(target=popserver.run).start()
    smtpserver.run()

if __name__ == "__main__":
    main()