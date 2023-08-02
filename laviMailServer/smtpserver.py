from threading import Thread
import socket
import database
import ssl

# Constants
HOST = 'localhost'
SMTP_PORT = 587

class Session:
    """Represents an SMTP session between a client and a server."""
    
    sender = ''  # The email address of the sender
    recipients = []  # The email addresses of the recipients
    message = ''  # The email message

    def __init__(self, client_sock):
        """
        Initialize a new SMTP session.

        Parameters:
        - client_sock: The client socket object used to communicate with the client
        """
        self.sock = client_sock

    def handleHelo(self, params):
        """
        Handle the HELO command.

        Parameters:
        - params: A list of parameters passed with the HELO command

        Returns:
        - A string response to send back to the client
        """
        return f"250 {params[0]} Hello {params[0]} [{HOST}], pleased to meet you\r\n"

    def handleMailFrom(self, params):
        """
        Handle the MAIL FROM command.

        Parameters:
        - params: A list of parameters passed with the MAIL FROM command

        Returns:
        - A string response to send back to the client
        """
        self.sender = params[0].strip('<>')
        return f"250 OK\r\n"

    def handleRcptTo(self, params):
        """
        Handle the RCPT TO command.

        Parameters:
        - params: A list of parameters passed with the RCPT TO command

        Returns:
        - A string response to send back to the client
        """
        self.recipients.append(params[0].strip('<>'))
        return f"250 OK\r\n"

    def handleData(self, params):
        """
        Handle the DATA command.

        Parameters:
        - params: A list of parameters passed with the DATA command

        Returns:
        - A string response to send back to the client
        """
        self.sock.send(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
        message = ''
        while True:
            data = self.sock.recv(1024).decode()
            message += data
            if message.endswith('\r\n.\r\n'):
                break
        self.message = message
        subject, date, body = extract_email_info(message)
        database.add_email(subject, self.sender, body, date, self.recipients, len(self.message))
        return f"250 OK\r\n"

    def handleNoop(self, params):
        """
        Handle the NOOP command.

        Parameters:
        - params: A list of parameters passed with the NOOP command

        Returns:
        - A string response to send back to the client
        """
        return f"250 OK\r\n"

    def handleQuit(self, params):
        """
        Handle the QUIT command.

        Parameters:
        - params: A list of parameters passed with the QUIT command

        Returns:
        - A string response to send back to the client
        """
        return f"221 Bye\r\n"

    def handleRset(self, params):
        """
        Handle the RSET command.

        Parameters:
        - params: A list of parameters passed with the RSET command

        Returns:
        - A string response to send back to the client
        """
        self.sender = ''
        self.recipients = []
        self.message = ''
        return f"250 OK\r\n"

    def handleUnknown(self, params):
        """
        Handles an unknown command by returning a '500 Unknown command' message.

        Args:
            params (list): A list of parameters passed with the command.

        Returns:
            str: The response message, '500 Unknown command\r\n'.
        """
        return f"500 Unknown command\r\n"

    dispatch = {
        'HELO': handleHelo,
        'MAIL FROM': handleMailFrom,
        'RCPT TO': handleRcptTo,
        'DATA': handleData,
        'NOOP': handleNoop,
        'QUIT': handleQuit,
        'RSET': handleRset
    }

def bind_and_listen():
    """
    Binds to the SMTP_PORT and listens for incoming connections from clients.
    Returns a wrapped SSL socket that encrypts all incoming and outgoing data.

    Returns:
        socket: An SSL socket object that is ready to accept incoming client connections.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SMTP_PORT))
    server.listen()
    # # Create an SSL context
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # # Load the private key and certificate files
    # context.load_cert_chain('server.crt', 'server.key', password='yoyo')
    # ssl_sock = context.wrap_socket(server, server_side=True)
    return server

def accept_clients(server):
    """
    Accepts incoming client connections and starts a new thread to handle each session.

    Args:
        server (socket): An SSL socket object that is bound and listening for incoming client connections.

    Returns:
        None
    """
    while True:
        client_sock, address = server.accept()
        # print(f"Connected with {str(address)}!")
        thread = Thread(target=handle_smtp_session, args=(client_sock, address))
        thread.start()

def handle_smtp_session(client, address):
    """
    Handles a single SMTP session with a client. Reads incoming data from the client socket,
    parses it into a command and parameters, executes the command and sends a response
    back to the client.

    Args:
        client (socket): A socket object representing the client connection.
        address (tuple): A tuple of (host, port) representing the client's address.

    Returns:
        None
    """
    session = Session(client)
    client.send(f"220 {HOST} ESMTP Service ready\r\n".encode())
    while True:
        msg = client.recv(1024).decode().replace('\r\n', '')
        print(f"client {str(address)}: {msg}")
        command, params = parse_request(msg)
        try:
            cmd = Session.dispatch[command]
        except KeyError:
            cmd = Session.handleUnknown
        response = cmd(session, params)
        print(f"server: {response}")
        client.send(response.encode())
        if command == 'QUIT':
            client.close()
            break

def parse_request(msg):
    words = msg.split(' ', 1)
    command = words[0].upper()
    if len(words) > 1:
        if ':' in words[1]:
            sub_words = words[1].split(':', 1)
            command += ' ' + sub_words[0].upper()
            params = [sub_words[1].strip()]
        else:
            params = words[1].split()
    else:
        params = []
    return command, params

def extract_email_info(email):
    lines = email.split("\r\n")
    subject = None
    date = None
    body = ""
    in_body = False
    for line in lines:
        if line.startswith("Subject: "):
            subject = line[9:]
        elif line.startswith("Date: "):
            date = line[6:]
        elif line == "":
            in_body = True
        elif in_body:
            body += line + "\r\n"
    return subject, date, body[:-3]

def run():
    server = bind_and_listen()
    print("smtp server is listening")
    accept_clients(server)