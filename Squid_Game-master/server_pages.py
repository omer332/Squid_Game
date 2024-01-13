import gc
import random
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime

from PIL import ImageTk, Image

from page_view_manager import PageViewManager, PageView, PAGE_TYPES, WaitingPage, GamePage, ErrorPage
from data_manager import DataManager, ClientRegisteredMessage, NumOFPlayersMessage, ListenOk, StartGame, \
    DollGonnaTurning, DollTurned, PlayerMovingStatus, PlayerFinishedHandleDollTurning, PlayerLose, CloseConnection, \
    GameFinished
from client_server import SocketCallBack, Server, Client


class ServerPlayersAmount(PageView, SocketCallBack):

    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is ListenOk:
            self.num_of_clients_listen += 1
            if self.num_of_clients_listen == self.num_of_clients:
                num_of_player_msg = NumOFPlayersMessage(num_of_players=self.num_of_clients)
                self.network.send(num_of_player_msg.full_msg_with_header())
        else:
            # save for later other messages.
            self.root.add_lost_packet(data)

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.network.close()
        self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error=error_msg)

    def __init__(self, root: PageViewManager, page_size):
        """
        The first page of the server.\n
        will get input num of players and create the clients.\n

        :param root: window root.
        :param page_size: window size.
        """
        self.combox = None
        self.label_welcome = None
        self.button_submit = None
        self.num_of_clients = -1
        self.num_of_clients_listen = 0
        self.network = root.get_network()
        super().__init__(root, page_size=page_size, title='Squid Game - Server')

        self.network.set_socket_call_back(self)
        self.network.connect_to_network()

    def set_and_actions(self):
        """
        Create the GUI widgets.
        """
        self._canvas.grid_anchor('center')
        self.root._play_sound()

        self.label_welcome = tk.Label(self._canvas, text="Choose Amount Of Players:", borderwidth=2, relief="solid",
                                      bg='grey', fg="white", font=("David bold", 13))
        self.label_welcome.grid(row=0, column=0, sticky='w', pady=(0, 5))

        self.combox = ttk.Combobox(self._canvas,
                                   values=[str(num) for num in range(1, DataManager.NUM_OF_MAX_CLIENTS + 1)],
                                   font=("David bold", 13))
        self.combox.grid(row=0, column=1, padx=(10, 5), sticky='n')
        self.combox.current(0)

        self.button_submit = tk.Button(self._canvas, text="submit", command=self._submit_action, borderwidth=2,
                                       relief="solid", bg='#FF337D', fg="white", font=("David bold", 13))
        self.button_submit.grid(row=4, column=0, sticky='w', pady=(0, 5))

        self.label_error = tk.Label(self._canvas, text="", borderwidth=2, relief="solid", bg='red', fg="black",
                                    font=("David bold", 13))

        tk.Button(self._canvas, text="Log Page", borderwidth=5,command=lambda :self.root.show_log_page(),
                                  relief="raised", bg='#02534c', fg="white", font=("David bold", 13)).place(x=5,y=5)

    def _submit_action(self):
        """
        Will execute in case the submit btn clicked.\n
        Verify the input (number of players is valid).\n
        Create Clients threads.\n
        Switch to next Page.
        """
        self.label_error.grid_forget()
        try:
            num_of_clients = int(self.combox.get())
            if num_of_clients not in range(1, DataManager.NUM_OF_MAX_CLIENTS + 1):
                self.label_error.config(
                    text=f"num of players must to be between {1} to {DataManager.NUM_OF_MAX_CLIENTS}")
                self.label_error.grid(row=5, column=0, columnspan=2, sticky='w')
                return
        except ValueError:
            self.label_error.config(text=f"input error expected range: {1} to {DataManager.NUM_OF_MAX_CLIENTS}")
            self.label_error.grid(row=5, column=0, sticky='w')
            return
        self.num_of_clients = num_of_clients
        for i in range(0, num_of_clients):
            client_th = threading.Thread(target=make_new_client_flow, args=(i,))
            client_th.daemon = True
            client_th.start()
        self.network.connect_to_clients(num_of_clients)
        self.network.start_getting_data_thread()
        self.root.change_display_screen(PAGE_TYPES.SERVER_WAITING_PAGE, page_size="500x600")


def make_new_client_flow(id=0):
    """
    Client Threads.\n

    :param id: Client id.
    """
    client = Client(id=id)
    PageViewManager(network=client).display_screen(PAGE_TYPES.CLIENT_REGISTER)


class ServerWaitingPage(WaitingPage):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is ClientRegisteredMessage:
            client_msg = DataManager.MSG_TYPES[header](json_msg=context)
            self.users_list.append(client_msg)
            self.player_in_game.append(client_msg)
            self.show_player(len(self.users_list) - 1)
            self.current_num_of_players += 1

            if self.current_num_of_players == self.network.get_num_of_clients():
                self.add_start_game_btn()

        elif DataManager.MSG_TYPES[header] is CloseConnection:
            client_close_msg = DataManager.MSG_TYPES[header](json_msg=context)
            self.num_of_player = self.network.get_num_of_clients()
            self.show_num_of_players()
            if self.num_of_player == 0:
                self.destroy()
                self.network.close()
                self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error="All client left!")
            else:
                for user, user_views in self.users_labels.items():
                    if user.client_id == client_close_msg.id:
                        user_views[0].destroy()
                        user_views[1].destroy()
                        self.current_num_of_players -= 1
                        self.player_in_game.remove(user)

                if self.current_num_of_players == self.network.get_num_of_clients():
                    self.add_start_game_btn()
        else:
            # save for later other messages.
            self.root.add_lost_packet(data)

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.network.close()
        self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error=error_msg)

    def __init__(self, root: PageViewManager, page_size):
        """
        The page will show the Clients' data.\n
        The server will start the game when all the clients finish registrations.\n

        :param root: the window.
        :param page_size: window size.
        """
        self.start_game_btn = None
        self.current_num_of_players = 0
        self.player_in_game = []
        super().__init__(root, page_size=page_size)
        tk.Button(self._canvas, text="Log Page", borderwidth=5,command=lambda :self.root.show_log_page(),
                                  relief="raised", bg='#673ab7', fg="white", font=("David bold", 13)).place(x=390,y=5)
        self.num_of_player = self.network.get_num_of_clients()
        self.show_num_of_players()

    def add_start_game_btn(self):
        """
        add button: start game.
        """
        self.start_game_btn = tk.Button(self.frame_scroll, text="Start Game", command=self.start_game, borderwidth=3,
                                        relief="raised", bg='#f4d056', fg="black", font=("David bold", 13))
        self.start_game_btn.grid(row=len(self.users_list) + 1, column=0, sticky='w', pady=(20, 15))

    def start_game(self):
        """
        change the page to the ServerGamePage.
        """
        self.root.change_display_screen(PAGE_TYPES.SERVER_GAME_PAGE, clients_data=self.player_in_game)


class ServerGamePage(GamePage):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is PlayerMovingStatus:
            self.player_status(DataManager.MSG_TYPES[header](json_msg=context))

        elif DataManager.MSG_TYPES[header] is CloseConnection:
            client_msg = DataManager.MSG_TYPES[header](json_msg=context)
            self.network.send(PlayerLose(id=client_msg.id).full_msg_with_header())
            self.kill_player(client_msg.id)

        elif DataManager.MSG_TYPES[header] is PlayerFinishedHandleDollTurning:
            player_status = DataManager.MSG_TYPES[header](json_msg=context)
            if player_status.is_lose:
                self.network.send(PlayerLose(id=player_status.id).full_msg_with_header())
                self.kill_player(player_status.id)
            else:
                self.clients_finish_handle_turning += 1
            if self.clients_finish_handle_turning == len(self.players):
                time.sleep(1)
                self.network.send(DollTurned(is_front=False).full_msg_with_header())
                self.turn_doll_img("doll_back.png")
                self.forget_lose_players()
                self.clients_finish_handle_turning = 0
                turning_time = random.randint(3, 7)
                self.th = time.time()
                self.is_finish_turning = True

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.network.close()
        self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error=error_msg)

    def __init__(self, root: PageViewManager, page_size, clients_data=None):
        """
        The Server game page.\n

        :param root: window root.
        :param page_size: window size.
        :param clients_data: players info.
        """
        self.th = None
        self.clients_finish_handle_turning = 0
        self.is_finish_turning = True
        super().__init__(root, page_size=page_size, clients_data=clients_data)
        self.network.send(StartGame().full_msg_with_header())
        th = threading.Thread(target=self.doll_turning)
        th.daemon = True
        th.start()

    def resize_window(self, width, height):
        super().resize_window(width, height)
        tk.Button(self.frame_doll, text="Log Page", borderwidth=5, command=lambda: self.root.show_log_page(),
                  relief="raised", bg='#aff1ff', fg="black", font=("David bold", 13)).place(x=5, y=5)

    def doll_turning(self):
        """
        Doll turning thread.\n
        Will turn the doll random and send to clients.\n
        In case the game finish -> will tell the clients, write to log and switch to LogPage.
        """
        time.sleep(3)

        turning_time = random.randint(3, 7)
        self.th = time.time()
        while len(self.players) != 0:
            time.sleep(1)
            if self.is_finish_turning:
                if self.th + turning_time - 2 <= time.time():
                    self.network.send(DollGonnaTurning().full_msg_with_header())

                    time.sleep(0.5)

                    self.network.send(DollTurned(is_front=True).full_msg_with_header())
                    self.turn_doll_img("doll_front.png")
                    self.is_finish_turning = False

        if len(self.win_players) > 0:
            self.network.send(GameFinished().full_msg_with_header())

        self.write_game_result_to_log()
        self.root.change_display_screen(PAGE_TYPES.SERVER_SETTING_PAGE,alive_clients=self.win_players)

    def close_all_threads(self):
        """
        Closing Server game page threads.
        """
        self.network.set_socket_call_back(None)
        self.players = []
        self.is_alive = False
        self.is_allowed_to_move = False
        self.is_moving = False

    def write_game_result_to_log(self):
        """
        Write the specific game's result to the log file.
        """
        msg = DataManager.LOG_START_NAME + "\n"
        today = datetime.now()
        msg += today.strftime("%d-%m-%Y %H:%M\n")
        msg += f"{len(self.win_players) + len(self.lose_players)}\n"
        msg += DataManager.LOG_START_WINNERS + "\n"
        for winner in self.win_players:
            msg += f"{winner.name}\n"
        msg += DataManager.LOG_START_LOSERS + "\n"
        for loser in self.lose_players:
            msg += f"{loser.name}\n"
        try:
            with open(DataManager.LOG_FILE_NAME, "a+") as file:
                file.write((msg))
        except:
            self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error="Failed During open Log file")


class ServerLogPage(PageView):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        pass

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.network.close()

    def __init__(self, root: PageViewManager, page_size):
        """
        The page display the log file.\n

        :param root: window root.
        :param page_size: window size.
        """
        self.scBar = None
        self.frame_scroll = None
        self.network = root.get_network()
        self.current_canvas = None
        self.th = threading.Thread(target=self.safe_reading_log)
        self.th.daemon = True
        super().__init__(root, page_size="945x700", title="Server - Log Page", img_background_name="back_finished.png")


    def set_and_actions(self, width=500, height=500):
        """
        Create the GUI widgets.
        """
        self.configure(background="#181617")
        self.frame_scroll = tk.Frame(self._canvas, background="#181617")
        self.frame_scroll.pack(fill=tk.BOTH, expand=1)

        self.scBar = ttk.Scrollbar(self._canvas, orient=tk.VERTICAL, command=self._canvas.yview)
        self.scBar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.configure(yscrollcommand=self.scBar.set, background="#181617")
        self._canvas.bind('<Configure>', lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        tk.Button(self._canvas, text="Back", borderwidth=5,command=lambda :self.root.hide_log_page(),
                                  relief="raised", bg='#f4d056', fg="black", font=("David bold", 13)).place(x=0,y=0)

        self.current_canvas= self._canvas.create_window((0, 0), window=self.frame_scroll, anchor="nw")

        self.th.start()



    def safe_reading_log(self):
        gc.disable()
        self.read_log()

    def read_log(self):
        """
        read the log file and add the data to a Table GUI widget.
        """
        try:
            with open(DataManager.LOG_FILE_NAME, "r") as file:
                log_data = file.read()
        except Exception as e:
            self._canvas.delete(self.current_canvas)
            self._canvas.grid_anchor("center")
            self.frame_scroll.forget()
            self.scBar.forget()
            tk.Label( self._canvas, text="There is no Log File", borderwidth=2,
                     relief="solid", bg='#181617', fg="white", font=("David bold", 26))\
                .grid(row=0, column=0, sticky='nw')
            return

        try:
            games_data = log_data.split(DataManager.LOG_START_NAME)
            games_data = list(filter(lambda line: line != '', games_data))

            tk.Label(self.frame_scroll, width=20, fg='white', borderwidth=2, relief="solid", bg="black",
                     font=('Arial', 16, 'bold'), text="Date").grid(row=0, column=0, sticky='nw')
            tk.Label(self.frame_scroll, width=20, fg='white', borderwidth=2, relief="solid", bg="black",
                     font=('Arial', 16, 'bold'), text="Number of Players").grid(row=0, column=1, sticky='nw')
            tk.Label(self.frame_scroll, width=30, fg='white', borderwidth=2, relief="solid", bg="black",
                     font=('Arial', 16, 'bold'), text="Game Results").grid(row=0, column=2, sticky='nw')

            for row, game_data in enumerate(games_data):
                game_data_lst = list(filter(lambda line: line != '', game_data.split("\n")))

                date_current_game = tk.Label(self.frame_scroll, width=20, fg='black', borderwidth=2, relief="solid",
                                             bg="white",
                                             font=('Arial', 16, 'bold'), text=game_data_lst[0])
                date_current_game.grid(row=row + 1, column=0, sticky='nw')
                num_of_players_current_game = tk.Label(self.frame_scroll, width=20, fg='black', borderwidth=2,
                                                       relief="solid", bg="white",
                                                       font=('Arial', 16, 'bold'), text=game_data_lst[1])
                num_of_players_current_game.grid(row=row + 1, column=1, sticky='nw')
                num_of_players = int(game_data_lst[1])
                date_current_game.configure(height=num_of_players + 1)
                num_of_players_current_game.configure(height=num_of_players + 1)
                game_data_lst.pop(0)
                game_data_lst.pop(0)
                its_winners_time = True
                players_results = ""
                winner_index = 1
                for line in range(0, num_of_players+2):
                    if game_data_lst[line] == DataManager.LOG_START_WINNERS:
                        its_winners_time = True
                    elif game_data_lst[line] == DataManager.LOG_START_LOSERS:
                        its_winners_time = False
                    else:
                        if its_winners_time:
                            players_results += f"{winner_index}. {game_data_lst[line]}\n"
                            winner_index+=1
                        else:
                            players_results += f"Died: {game_data_lst[line]}\n"

                tk.Label(self.frame_scroll, width=30, height=num_of_players + 1, fg='black', borderwidth=2,
                        relief="solid", bg="white",
                        font=('Arial', 16, 'bold'),
                        text=players_results).grid(row=row + 1, column=2, sticky='nw')


        except Exception as e:
            self._canvas.delete(self.current_canvas)
            self._canvas.grid_anchor("center")
            self.frame_scroll.forget()
            self.scBar.forget()
            tk.Label( self._canvas, text="Log file contains a wrong data", borderwidth=2,
                     relief="solid", bg='#181617', fg="white", font=("David bold", 26))\
                .grid(row=0, column=0, sticky='nw')


class ServerErrorPage(ErrorPage):
    def __init__(self, root: PageViewManager, page_size, error=None):
        """
        The page display the occurred error and switch to the LogPage in case of button clicked.\n

        :param root: window root.
        :param page_size: window size.
        :param error: the error input.
        """
        if error is not None:
            error += ", Moving to log page"
        super().__init__(root, page_size, error=error)

        self.root.title("Server - Error Page")
        tk.Button(self._canvas, text="Setting Page", borderwidth=3,command=self.finish,
                                   relief="raised", bg='#0078d7', fg="white", font=("David bold", 15))\
                        .grid(row=1, column=0, sticky='n', pady=(150, 5))

    def finish(self):
        """
        Switch to Log page.
        """

        self.root.change_display_screen(PAGE_TYPES.SERVER_SETTING_PAGE)


class ServerSettingPage(PageView, SocketCallBack):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is CloseConnection:
            id = DataManager.MSG_TYPES[header](json_msg=context).id
            if self.alive_clients is not None:
                self.alive_clients= list(filter(lambda player:player.id != id ,self.alive_clients))

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.network.close()
        self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error=error_msg)

    def __init__(self, root: PageViewManager, page_size, alive_clients=None):
        """
        The page give the Server the option to move to Log file or a new game.\n

        :param root: window root.
        :param page_size: window size.
        """
        self.alive_clients = alive_clients
        self.network = root.get_network()
        self.network.set_socket_call_back(self)
        self.error_msg = None
        super().__init__(root, page_size, title='Server -  Setting Page',img_background_name='setting_page_back.png')

        self._canvas.grid_anchor('n')
        tk.Button(self._canvas, text="Log Page", borderwidth=3,command=self.to_log_page,
                                  relief="raised", bg='#33bacd', fg="white", font=("David bold", 15))\
                       .grid(row=0, column=0, sticky='n', pady=(150, 5),padx=(50, 50))

        tk.Button(self._canvas, text="New Game", borderwidth=3,command=self.create_new_game,
                                  relief="raised", bg='#33bacd', fg="white", font=("David bold", 15))\
                       .grid(row=0, column=1, sticky='n', pady=(150, 5),padx=(0, 50))

    def create_new_game(self):
        if self.alive_clients is None or len(self.alive_clients) == 0:
            self.network.close()
            self.root.set_network(Server())
            self.root.change_display_screen(PAGE_TYPES.SERVER_PLAYERS_AMOUNT)
            return

        #parsing players list
        players_in_game = list(map(lambda player: ClientRegisteredMessage(client_name=player.name, client_id=player.id, avatar_index=player.avatar_index, is_pc_player=player.is_pc_player), self.alive_clients))
        self.root.change_display_screen(PAGE_TYPES.SERVER_GAME_PAGE, clients_data=players_in_game)

    def to_log_page(self):
        try:
            self.root.show_log_page()
        except Exception as e:
            print(str(e))



if __name__ == "__main__":
    """
        Server Pages in case you want to debug:
            SERVER_PLAYERS_AMOUNT
            SERVER_WAITING_PAGE
            SERVER_GAME_PAGE
            SERVER_ERROR_PAGE
            SERVER_LOG_PAGE

        Simulating Error !!! Program should run from main.py for the correct flow
        Simulating Server to open without sending the clients details, and expecting Error  
        Error page will close automatically after 2 seconds and will move to Log Page!!!!!!
    """
    pass
