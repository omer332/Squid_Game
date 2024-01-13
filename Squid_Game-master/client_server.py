import socket
import threading
import time

from data_manager import DataManager, KillAll, CloseConnection

# Max size of a message.
RECV_SIZE_MAX = 4096


class SocketCallBack:
    def __init__(self):
        """
        Callback interface for getting server & client threads messages\n
        Callback users should extand for this class & override the functions.
        """
        pass

    def get_data_from_socket(self, data):
        """
        Server/client updates it's listeners in the data received.

        :param data: The message the client/server received.
        """
        pass

    def socket_error(self, error_msg):
        """
        In case the server/client is getting error, update the listener.

        :param error_msg: The error's context message.
        """
        pass


class Server:

    def __init__(self, port=5050, socket_call_back=None):
        """
        Server's set-up.\n
        ---Attributes---
            host:   IP address.\n
            socket: Server's socket.\n
            my_clients: Server's clients, in a directory, which includes conn-address.\n
            id: Server's id.\n
            get_data_thread: Thread in charge to get information from Client's the whole program time.
        :param port: Port for connection.
        :param socket_call_back: In case of updating the listeners (if there's any).
        """
        self.__host = socket.gethostbyname(socket.gethostname())
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__my_clients = {}
        self.__socket_call_back = socket_call_back
        self.__id = DataManager.SERVER_ID
        self.__get_data_threads = []
        self.is_alive = True

    def set_socket_call_back(self, socket_call_back):
        """
        Set socket's callback for update the listener.
        :param socket_call_back: The new listener.
        """
        self.__socket_call_back = socket_call_back

    def start_getting_data_thread(self):
        """
        When having clients, start getting data.
        """
        for get_client_data_th in self.__get_data_threads:
            get_client_data_th.daemon=True
            get_client_data_th.start()

    def connect_to_network(self):
        """
         Connecting the server's socket, and start listening to the port.
         :exception Socket's error
        """
        try:
            self.__socket.bind((self.__host, self.__port))
            self.__socket.listen()
        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def connect_to_clients(self, num_of_clients=1):
        """
        Connecting clients as requested from the user.
        :param num_of_clients: Amount of clients to connect.
        :exception Socket's error
        """
        try:
            for i in range(0, num_of_clients):
                conn, address = self.__socket.accept()
                if address not in self.__my_clients:
                    self.__my_clients[address] = conn
                    self.__get_data_threads.append(threading.Thread(target=self.get, args=(conn,address)))
        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def send(self, data):
        """
        Server is sending to all of it's clients a message.
        :param data: Message's context
        :exception Socket's error
        """
        try:
            for client_conn in self.__my_clients.values():
                client_conn.sendall(str.encode(data))
        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))


    def get(self, client_conn,address):
        """
        Server is waiting for messages from clients.\n
        Once a message is recieved, the server is updating the clients & call-back is being updated.
        In one RECV action a multiple messages can be received
        :exception Socket's error
        """
        try:
            is_client_alive = True
            while self.is_alive:
                data = client_conn.recv(RECV_SIZE_MAX).decode()
                packets_list = data.split(DataManager.SPLIT_MESSAGES)
                if DataManager.CLOSE_CONNECTION in data:
                    client_conn.close()
                    self.__my_clients.pop(address)
                    is_client_alive = False
                if len(self.__my_clients) > 0:
                    self.send(data)
                for packet in packets_list:
                    if packet != "":
                        if self.__socket_call_back is not None:
                            self.__socket_call_back.get_data_from_socket(packet)
                if is_client_alive is False:
                    return

        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def get_id(self):
        """
        :return: Server's id
        """
        return self.__id

    def get_num_of_clients(self):
        """
        :return: Size of my_client's list
        """
        return len(self.__my_clients)

    def close(self):
        """
         Close server socket and kill clients
        """
        if self.is_alive is False:
            return

        self.is_alive = False

        if len(self.__my_clients) > 0:
            self.send(KillAll().full_msg_with_header())
            self.__socket.close()
            time.sleep(2.3)
        else:
            self.__socket.close()

        self.__socket_call_back = None

class Client:
    def __init__(self, port=5050, socket_call_back=None, id=0):
        """
        Client's set-up.\n
        ---Attributes---
            host:   IP address.\n
            socket: Client's socket.\n
            get_data_thread: Thread in charge to get information from server the whole program time.
        :param port: Port for connection.
        :param socket_call_back: In case of updating the listeners (if there's any).
        :param id: Client's id.
        """
        self.__host = socket.gethostbyname(socket.gethostname())
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket_call_back = socket_call_back
        self.__id = id
        self.__get_data_thread = threading.Thread(target=self.get)
        self.is_alive=True

    def start_getting_data_thread(self):
        """
        Start getting data from server.
        """
        self.__get_data_thread.daemon=True
        self.__get_data_thread.start()

    def set_socket_call_back(self, socket_call_back):
        """
         Set socket's callback for update the listener.
         :param socket_call_back: The new listener.
         """
        self.__socket_call_back = socket_call_back

    def connect_to_network(self):
        """
         Connecting the Client's socket, and start listening to the port.
         :exception Socket's error
        """
        try:
            self.__socket.connect((self.__host, self.__port))
        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def send(self, data):
        """
        Client is sending a message to server.
        :param data: Message's context
        :exception Socket's error
        """
        try:
            self.__socket.sendall(str.encode(data))
        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def get(self):
        """
        Client is waiting for messages from the server.\n
        Once a message is received, call-back is being updated.
        In one RECV action a multiple messages can be received
        :exception Socket's error
        """
        try:
            while self.is_alive:
                data = self.__socket.recv(RECV_SIZE_MAX).decode()
                packets_list = data.split(DataManager.SPLIT_MESSAGES)
                for packet in packets_list:
                    if packet != "":
                        if self.__socket_call_back is not None:
                            self.__socket_call_back.get_data_from_socket(packet)

        except Exception as e:
            if self.__socket_call_back is not None:
                self.__socket_call_back.socket_error(str(e))

    def get_id(self):
        """
        :return: Client's id.
        """
        return self.__id

    def close(self):
        """
         Close client socket and send a message before if needed
        """
        if self.is_alive is False:
            return

        self.send(CloseConnection(id=self.__id).full_msg_with_header())

        self.is_alive = False
        self.__socket_call_back = None


