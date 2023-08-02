import win32com.client
import pythoncom
import os
import requests
import hashlib
import sqlite3
import time

DIR_NAME = "Temp Files"
DB_NAME = "info.db"

# def get_md5(fname):
#     hash_md5 = hashlib.md5()
#     with open(fname, "rb") as f:
#         for chunk in iter(lambda: f.read(4096), b""):
#             hash_md5.update(chunk)
#     return hash_md5.hexdigest()

def search_malicious_file(mail):
    if len(mail.Attachments) == 0:
        return
    for file in mail.Attachments:
        file.SaveAsFile(os.path.join(os.getcwd() + "\\" + DIR_NAME, file.FileName))
        url = 'https://www.virustotal.com/vtapi/v2/file/scan'
        params = {'apikey': '3ba93fa402a55711d973c4a5d33dc72f60e34380edc534bd50dd72042055698a'}
        stream = open(os.path.join(os.getcwd() + "\\" + DIR_NAME, file.FileName), 'rb')
        files = {'file': (file.FileName, stream)}
        response = requests.post(url, files=files, params=params)
        scan_id = response.json()["scan_id"]
        params['resource'] = scan_id
        url = 'https://www.virustotal.com/vtapi/v2/file/report'
        response = requests.get(url, params=params)
        while response.json()["verbose_msg"] == "Your resource is queued for analysis":
            print("Trying again")
            time.sleep(10)
            response = requests.get(url, params=params)
            print(response.text)
        stream.close()
        if response.json()["positives"] > 0:
            print("Got It!!!")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(f'INSERT INTO EVENTS(address, hasMaliciousFiles, receivedTime) VALUES("{mail.SenderName}", True, "{mail.ReceivedTime}")')
            conn.commit()
            conn.close()
            mail.Delete()
        os.remove(os.path.join(os.getcwd() + "\\" + DIR_NAME, file.FileName))
             

#Handler for Application Object
class Application_Handler(object):
    def OnNewMailEx(self, receivedItemsIDs):
        outlook = win32com.client.Dispatch("Outlook.Application").Session
        for id in receivedItemsIDs.split(","):
            mail = outlook.GetItemFromID(id)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(f'SELECT * FROM EVENTS WHERE address="{mail.SenderName}"')
            conn.commit()
            if len(c.fetchall()) != 0:
                mail.Delete()
                conn.close()
                break
            conn.close()
            if mail.Class == win32com.client.constants.olMail:
                search_malicious_file(mail)


def initiate_files():
    # create files directory if it doesn't exist
    os.makedirs(DIR_NAME, exist_ok=True)
    # create database if it doesn't exist
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS EVENTS(address TEXT PRIMARY KEY, hasMaliciousFiles INTEGER, receivedTime TEXT)')
    conn.commit()
    conn.close()

def main():
    initiate_files()
    outlook = win32com.client.DispatchWithEvents("Outlook.Application", Application_Handler)
    #Message loop
    pythoncom.PumpMessages()

if __name__ == "__main__":
    main()