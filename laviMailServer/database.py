import sqlite3
import hashlib
import email.mime.text
import email.utils

DB_NAME = "emails.db"

def initiate():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # create table for emails
    c.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            sender TEXT NOT NULL,
            body TEXT NOT NULL,
            date TEXT NOT NULL,
            size INTEGER NOT NULL,
            uid TEXT UNIQUE NOT NULL
        )
        ''')
    # create table for recipients
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
        ''')
    conn.commit()
    conn.close()

def get_emails_size_by_address(address):
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get the emails for the given recipient address
    c.execute("""
        SELECT size
        FROM emails
        JOIN recipients ON emails.id = recipients.email_id
        WHERE address = ?
    """, (address,))
    sizes = c.fetchall()
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    return [size[0] for size in sizes]

def get_count_and_total_size_of_emails_by_address(address):
     # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get the emails for the given recipient address
    c.execute('''
        SELECT COUNT(emails.id), SUM(emails.size) 
        FROM emails 
        JOIN recipients ON emails.id = recipients.email_id 
        WHERE recipients.address = ?''', (address,))
    # Fetch the results and assign them to variables
    num_of_emails, total_size = c.fetchone()
    if total_size == None:
        total_size = 0
    # Close the database connection
    conn.close()
    # Return the number of emails and total size as a tuple
    return num_of_emails, total_size

def add_email(subject, sender, body, date, recipients, size):
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    last_id = c.lastrowid
    if last_id == None:
        last_id = 0
    # remove duplicates from the recipients
    recipients = list(set(recipients))
    # create uid using the new id, subject, sender and size of the email
    uid = hashlib.md5((str(last_id + 1) + subject + sender + str(size)).encode('utf-8')).hexdigest()
    # Insert the email into the emails table
    c.execute("""
        INSERT INTO emails (subject, sender, body, date, size, uid)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (subject, sender, body, date, size, uid))
    # Get the ID of the inserted email
    email_id = c.lastrowid
    # Insert the recipients into the recipients table
    for recipient in recipients:
        c.execute("""
            INSERT INTO recipients (email_id, address)
            VALUES (?, ?)
        """, (email_id, recipient))
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def get_uid_by_index_and_address(index, address):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT uid 
        FROM emails 
        JOIN recipients ON emails.id = recipients.email_id 
        WHERE recipients.address = ?
        LIMIT 1 OFFSET ?
        ''', (address, index - 1))
    uid = c.fetchone()
    conn.close()
    return uid

def get_uid_list_by_address(address):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT uid 
        FROM emails 
        JOIN recipients ON emails.id = recipients.email_id 
        WHERE recipients.address = ?
        ''', (address,))
    uid_list = c.fetchall()
    conn.close()
    return [uid[0] for uid in uid_list]

def get_email_by_index_and_address(index, address):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT subject, sender, body, date
        FROM emails 
        JOIN recipients ON emails.id = recipients.email_id 
        WHERE recipients.address = ?
        LIMIT 1 OFFSET ?
        ''', (address, index - 1))
    subject, sender, body, date = c.fetchone()
    conn.close()
    return create_email_message(subject, sender, body, date)

def create_email_message(subject, sender, body, date):
    # Create a MIME text message object
    msg = email.mime.text.MIMEText(body)

    # Set the message headers
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender
    msg['Date'] = date
    # Return the message in string format
    return msg.as_string()