from threading import Thread
import socket
import database
import ssl

HOST = 'localhost'
POP3_PORT = 110

class Session:
    """
    Class representing a POP3 session. It handles various commands sent by the client.
    """

    address = ''

    def handleUser(self, params):
        """
        Handle the USER command.
        USER command is used to specify the username to log into the email account.

        :param params: List of parameters passed with the USER command.
        :return: Response string for the USER command.
        """
        self.address = params[0]
        return "+OK user accepted\r\n"

    def handlePass(self, params):
        """
        Handle the PASS command.
        PASS command is used to specify the password for the email account.

        :param params: List of parameters passed with the PASS command.
        :return: Response string for the PASS command.
        """
        return "+OK pass accepted\r\n"

    def handleStat(self, params):
        """
        Handle the STAT command.
        STAT command is used to get the status of the mailbox.

        :param params: List of parameters passed with the STAT command.
        :return: Response string for the STAT command.
        """
        num_of_mails, total_size = database.get_count_and_total_size_of_emails_by_address(self.address)
        return f"+OK {num_of_mails} {total_size}\r\n"

    def handleList(self, params):
        """
        Handle the LIST command.
        LIST command is used to get the list of messages in the mailbox.

        :param params: List of parameters passed with the LIST command.
        :return: Response string for the LIST command.
        """
        sizes = database.get_emails_size_by_address(self.address)
        if (len(params) != 0):
            index = int(params[0])
            return f"+OK {index} {sizes[index-1]}\r\n"
        num_of_mails, total_size = database.get_count_and_total_size_of_emails_by_address(self.address)
        messages_list = '\r\n'.join([f"{i} {size}" for i, size in enumerate(sizes, start=1)])+'\r\n.\r\n'
        return f'+OK {num_of_mails} messages ({total_size} octets)\r\n' + messages_list 

    def handleTop(self, params):
        """
        Handle the TOP command.
        TOP command is used to retrieve the headers and a specified number of lines of the message text.

        :param params: List of parameters passed with the TOP command.
        :return: Response string for the TOP command.
        """
        message_index = int(params[0])
        num_lines = int(params[1])
        messages = database.get_emails_by_recipient(self.address)
        message = messages[message_index -1][0].replace('\\n','\n')
        headers, body = message.split('\n\n', 1)
        top_lines = '\n'.join(body.split('\n')[:num_lines])
        return headers + '\n' + top_lines + '\r\n.\r\n'

    def handleRetr(self, params):
        """
        Handles the RETR command. The RETR command is used to retrieve a specific email
        message from the mail server.

        :param params: The parameters provided with the RETR command. It should contain a single value which
                       represents the index of the email to retrieve.
        :return: A string in the format of "+OK [length of email in octets] octets\r\n[email content]\r\n.\r\n",
                 indicating the success of the retrieval and the content of the email.
        """
        mail = database.get_email_by_index_and_address(int(params[0]), self.address)
        return f"+OK {len(mail)} octets\r\n{mail}\r\n.\r\n"

    def handleDele(self, params):
        """
        The handleDele function is called to handle the DELE command from the client.
        This command allows the client to delete a specific message from the server.
        
        Args:
        params: The parameters of the DELE command, in this case, the message number.
        
        Returns:
        A string response indicating whether the message was deleted or not.
        """
        return "+OK message 1 deleted"
    
    def handleNoop(self, params):
        """
        The handleNoop function is called to handle the NOOP command from the client.
        This command does not perform any action and is used to test the connection.
        
        Args:
        params: The parameters of the NOOP command, which is not used in this function.
        
        Returns:
        A string response indicating that the NOOP command was received.
        """
        return "+OK\r\n"

    def handleQuit(self, params):
        """
        The handleQuit function is called to handle the QUIT command from the client.
        This command terminates the connection between the client and the server.
        
        Args:
        params: The parameters of the QUIT command, which is not used in this function.
        
        Returns:
        A string response indicating that the server is signing off.
        """
        return "+OK POP3 server signing off\r\n"

    def handleCapability(self, params):
        """
        The handleCapability function is called to handle the CAPA command from the client.
        This command returns a list of the capabilities that the server supports.
        
        Args:
        params: The parameters of the CAPA command, which is not used in this function.
        
        Returns:
        A string response indicating the capability list and the supported commands.
        """
        commands = '\r\n'.join(list(self.dispatch.keys()))
        return f"+OK Capability list follows\r\n{commands}\r\n.\r\n"

    def handleUidl(self, params):
        if len(params) != 0:
            return f"+OK {params[0]} {database.get_uid_by_index_and_address(int(params[0]), self.address)}"
        uid_list = database.get_uid_list_by_address(self.address)
        response_list = '\r\n'.join([f"{i} {uid}" for i, uid in enumerate(uid_list, start=1)])
        return f"+OK\r\n{response_list}\r\n.\r\n"

    """
    This dictionary dispatch maps POP3 commands to the corresponding handler functions. 
    Each key in the dictionary is a string representing a POP3 command, and the corresponding 
    value is a reference to the function that should handle that command.
    """
    dispatch = {
    'USER': handleUser,
    'PASS': handlePass,
    'STAT': handleStat,
    'LIST': handleList,
    'TOP': handleTop,
    'RETR': handleRetr,
    'DELE': handleDele,
    'NOOP': handleNoop,
    'QUIT': handleQuit,
    'CAPA': handleCapability,
    'UIDL': handleUidl
    }

def bind_and_listen():
    """
    This function creates a socket and binds it to the host and POP3 port specified in the global variables. 
    Then it starts listening for incoming connections on this socket.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, POP3_PORT))
    server.listen()
    # # Create an SSL context
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # # Load the private key and certificate files
    # context.load_cert_chain('server.crt', 'server.key', password='yoyo')
    # ssl_sock = context.wrap_socket(server, server_side=True)
    return server

def accept_clients(server):
    """
    This function waits for incoming connections to the server and starts a new thread for each client connection.
    The thread is started with the handle_pop_session function as the target.
    """
    while True:
        client_sock, address = server.accept()
        # print(f"Connected with {str(address)}!")
        thread = Thread(target=handle_pop_session, args=(client_sock, address))
        thread.start()

def handle_pop_session(client, address):
    """
    This function handles the POP3 session with a client. It starts by sending the '+OK POP3 server ready' message to the client,
    and then it enters a loop waiting for messages from the client. For each message, it tries to look up the corresponding command
    handler from the `Session.dispatch` dictionary, and calls the handler with the parameters specified in the client message. 
    If the command is not recognized, it sends an error message to the client.
    """
    session = Session()
    try:
        client.send(b'+OK POP3 server ready\r\n')
        command = ''
        while(command != 'QUIT'):
            msg = client.recv(1024).decode().replace('\r\n', '')
            print(f"client {str(address)}: {msg}")
            command = msg.split(' ')[0]
            params = msg.split(' ')[1:]
            try:
                cmd = Session.dispatch[command]
                res = cmd(session, params)
                print(f"server: {res}")
                client.send(res.encode())
            except KeyError:
                client.send(b"-ERR unknown command")
    finally:
        print(f"Client {address} disconnected")
        client.close()

def run():
    """
    This function is the entry point for the POP3 server. It initiates the database and starts the POP3 server.
    """
    server = bind_and_listen()
    print("pop server is listening")
    accept_clients(server)