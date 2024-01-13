import gc
import random
import signal
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk

import winsound
from PIL import ImageTk, Image
from enum import Enum
from PIL.Image import Resampling
from copy import deepcopy


from client_server import SocketCallBack, Client
from data_manager import DataManager, ClientRegisteredMessage, NumOFPlayersMessage, ListenOk, PlayerMovingStatus, \
    StartGame, DollGonnaTurning, DollTurned, PlayerFinishedHandleDollTurning, KillAll, DataMessage, Ping, \
    CloseConnection


class PAGE_TYPES(Enum):
    """
    the Enum contain the pages you can create for Server & Clients
    """
    SERVER_PLAYERS_AMOUNT = 0
    CLIENT_REGISTER = 1
    CLIENT_WAITING_PAGE = 2
    SERVER_WAITING_PAGE = 3
    CLIENT_GAME_PAGE = 4
    SERVER_GAME_PAGE = 5
    CLIENT_LOST_PAGE = 6
    CLIENT_GAME_FINISHED_PAGE = 7
    CLIENT_ERROR_PAGE = 8
    SERVER_ERROR_PAGE = 9
    SERVER_LOG_PAGE = 10
    SERVER_SETTING_PAGE = 11


class PageViewManager(tk.Tk):
    def __init__(self, network):
        """
        the root TK window for every client or server.
        manage the window and the frames inside.

        ---Attributes---.
            frame: the main window frame.\n
            network: Client or Server object.\n
            lost_packets: packets (messages between server & clients) we need to keep for later (in case we are switching main frame).\n
            is_alive: in charge to verify we didn't destroy the window more than once.\n
            thread_sound: in charge to play the welcome song.\n
            is_sound_on: verify that thread_sound wont play more than once.\n
        :param network: the Server or Client object.
        """
        super().__init__()
        self.__frame = None
        self.__frame = None
        self.__network = network
        self.lost_packets = []
        self.attributes("-topmost", True)
        self.is_alive = True
        self._thread_sound = threading.Thread(target=self._sound_on)
        self._thread_sound.daemon = True
        self.is_sound_on = False
        self.save_frame = None

    def display_screen(self, page_type, page_size='500x500', **kwargs):
        """
        will create a new window.
        if the window already exists we are only switch frame.

        :param page_type: type (Enum-PAGE_TYPES) the page we want.
        :param page_size: type (str, like:'500x500') responsible window size.
        :param **kwargs: in case the page get parametrs.
        """
        self.create_display_screen(page_type, page_size,
                                   **kwargs) if self.__frame is None else self.change_display_screen(
            page_type, page_size, **kwargs)

    def change_display_screen(self, page_type, page_size='500x500', **kwargs):
        """
        will change the window's main frame and destroy the last main frame if needed.

        :param page_type: type (Enum-PAGE_TYPES) the page we want.
        :param page_size: type (str, like:'500x500') responsible window size.
        :param **kwargs: in case the page get parametrs.
        """
        if self.__frame is not None:
            self.__frame.destroy()
        try:
            self.__frame = self.get_view_frames_dict()[page_type](self, page_size=page_size, **kwargs)
            self.__frame.pack(fill=tk.BOTH, expand=1)
        except: # will raise during destroy
            pass

    def create_display_screen(self, page_type, page_size, **kwargs):
        """
        set icon & activate the main loop.

        :param page_type: type (Enum-PAGE_TYPES) the page we want.
        :param page_size: type (str, like:'500x500') responsible window size.
        :param **kwargs: in case the page get parametrs.
        """
        self.iconbitmap('icon1.ico')
        self.change_display_screen(page_type, page_size, **kwargs)
        self.mainloop()

    def get_view_frames_dict(self):
        """
        :return: dictionary {Enum (PAGE_TYPES : some PageClass }
        """
        from server_pages import ServerPlayersAmount, ServerWaitingPage, ServerGamePage, ServerErrorPage, ServerLogPage, ServerSettingPage
        from client_pages import ClientRegister, ClientGamePage, ClientLostPage, ClientGameFinishedPage, ClientErrorPage
        return {PAGE_TYPES.SERVER_PLAYERS_AMOUNT: ServerPlayersAmount,
                PAGE_TYPES.CLIENT_REGISTER: ClientRegister,
                PAGE_TYPES.CLIENT_WAITING_PAGE: WaitingPage,
                PAGE_TYPES.SERVER_WAITING_PAGE: ServerWaitingPage,
                PAGE_TYPES.SERVER_GAME_PAGE: ServerGamePage,
                PAGE_TYPES.CLIENT_GAME_PAGE: ClientGamePage,
                PAGE_TYPES.CLIENT_LOST_PAGE: ClientLostPage,
                PAGE_TYPES.CLIENT_ERROR_PAGE: ClientErrorPage,
                PAGE_TYPES.CLIENT_GAME_FINISHED_PAGE: ClientGameFinishedPage,
                PAGE_TYPES.SERVER_ERROR_PAGE: ServerErrorPage,
                PAGE_TYPES.SERVER_LOG_PAGE: ServerLogPage,
                PAGE_TYPES.SERVER_SETTING_PAGE: ServerSettingPage

                }

    def get_network(self):
        """
        :return: network: Server or Client object.
        """
        return self.__network

    def set_network(self, network):
        """
        :param: network: Server or Client object.
        """
        self.__network = network

    def add_lost_packet(self, packet):
        """
        :param packet: save messages between Clients & Server.
        """
        self.lost_packets.append(packet)

    def get_lost_packets_list(self):
        """
        :return: lost_packets: messages we saved between Clients & Server
        """
        return deepcopy(self.lost_packets)

    def clear_lost_packets_list(self):
        """
        Clear messages we saved (after we finish to use them).
        """
        self.lost_packets.clear()

    def destroy(self):
        """
        destroy the window.\n
        close the network - Client or Server.\n
        verify in case the page have threads he will close them.
        """
        if hasattr(self.__frame,"read_log"):
            self.hide_log_page()
            return 
        if self.is_alive is False:
            return

        self.is_alive = False
        self.__network.close()
        if hasattr(self.__frame,"close_all_threads"):
            self.__frame.close_all_threads()
        self.exit()

    def exit(self):
        """
        execute TK().destroy().\n
        exception it will raise exception in case we are not in main loop
        """
        try:
            super().destroy()
        except:  # will raise main loop exception
            pass

    def kill_all(self):
        """
        close all threads in case some threads run.
        """
        signal.raise_signal(signal.SIGTERM)

    def _play_sound(self):
        """
        in case sound off -> start sound thread
        """
        if self.is_sound_on is False:
            self._thread_sound.start()

    def _sound_on(self):
        """
        play sound
        """
        try:
            self.is_sound_on = True
            while True:
                winsound.PlaySound('welcome_sound.wav', winsound.SND_FILENAME)
            self.is_sound_on=False
        except:
            pass

    def show_log_page(self):
        self.__frame.forget()
        self.save_frame = self.__frame
        try:
            self.__frame = self.get_view_frames_dict()[PAGE_TYPES.SERVER_LOG_PAGE](self, page_size="500x500")
            self.__frame.pack(fill=tk.BOTH, expand=1)
        except: # will raise during destroy
            pass

    def hide_log_page(self):
        self.__frame.destroy()
        self.geometry("500x500")
        self.__frame = self.save_frame
        if self.__frame is not None:
            self.__frame.pack(fill=tk.BOTH, expand=1)


class PageView(tk.Frame):
    def __init__(self, root, page_size='500x500', title='Squid Game',
                 img_background_name='back_start_game.png'):
        """
        the main frame of the window, type -> frame.\n

        :param root: the window master (type:TK).
        :param img_background_name: the frame background img.
        :param title: window title.
        """
        super().__init__(root, bg="black")

        self.root = root
        self.root.geometry(page_size)
        self.root.title(title)
        #canvas will present the img background
        self._canvas = tk.Canvas(self)
        self._canvas.pack(fill="both", expand=1)
        self._my_img_background = img_background_name
        self._bg_photo = None
        self.error_func = 0
        self.is_error_occurred = False

        self.set_and_actions()
        #will execute every time the window will change
        self.bind('<Configure>', self.set_background_photo)

    def set_and_actions(self):
        """
        will override in the pages that extends this page
        """
        pass

    def set_background_photo(self, e):
        """
        make background img resize.\n
        if the frame need to use the new size of the frame -> send the new size.

        :param e: event window size change
        """
        img = Image.open(self._my_img_background).resize((e.width, e.height), Resampling.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(img, master=self.root)
        self._canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")
        if hasattr(self, "resize_window"):
            self.resize_window(e.width, e.height)

    def error(self, error_msg):
        """
        will close the current frame and change to ServerErrorPage.

        :param error_msg: the error str
        """
        super().destroy()
        if self.error_func == 0:
            if self.root.get_network().get_id() == DataManager.SERVER_ID:
                self.root.change_display_screen(PAGE_TYPES.SERVER_ERROR_PAGE, error=error_msg)
                self.root.get_network().close()
            else:
                self.root.get_network().set_socket_call_back(self)
            self.error_func += 1


class WaitingPage(PageView, SocketCallBack):

    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is KillAll:
            self.is_error_occurred = True
            #self.destroy()
            self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

        elif DataManager.MSG_TYPES[header] is CloseConnection:
            client_close_msg = DataManager.MSG_TYPES[header](json_msg=context)
            self.num_of_player -= 1
            self.show_num_of_players()

            for user, user_views in self.users_labels.items():
                if user.client_id == client_close_msg.id:
                    user_views[0].destroy()
                    user_views[1].destroy()
                    self.player_in_game.remove(user)

        elif DataManager.MSG_TYPES[header] is ClientRegisteredMessage:
            client_msg = DataManager.MSG_TYPES[header](json_msg=context)
            self.users_list.append(client_msg)
            self.player_in_game.append(client_msg)
            self.show_player(len(self.users_list) - 1)

        elif DataManager.MSG_TYPES[header] is NumOFPlayersMessage:
            self.num_of_player = DataManager.MSG_TYPES[header](json_msg=context).num_of_players
            self.show_num_of_players()
        elif DataManager.MSG_TYPES[header] is StartGame and self.network.get_id != DataManager.SERVER_ID:
            self.root.change_display_screen(PAGE_TYPES.CLIENT_GAME_PAGE, clients_data=self.player_in_game, title=f"{self.identifier_name}")
        elif DataManager.MSG_TYPES[header] is ListenOk:
            pass
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
        #self.destroy()
        self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

    def __init__(self, root: PageViewManager, page_size, title = None):
        """
        the page will show the Clients that register the game.\n
        Server and Client Wating Page extend this class.

        :param root: the window.
        :param page_size: window size.
        :param title: window title.
        """
        self.label_num_of_player = None
        self.users_list = []
        self.users_labels = {}
        self.avatars_list = []
        self.num_of_player = 0
        self.network = root.get_network()
        self.identifier_name = title
        self.player_in_game = []

        if title is None:
            title = f"Waiting Page - Player {self.network.get_id()}" if isinstance(self.network,
                                                                              Client) else f"Waiting Page - Server"
        else:
            title = f"Waiting Page - {title}"
        super().__init__(root, page_size=page_size, title=title, img_background_name="back_waiting.png")

        self.network.set_socket_call_back(self)
        lost_packets_list = self.root.get_lost_packets_list()
        self.root.clear_lost_packets_list()
        self.handle_lost_packets(lost_packets_list)

    def handle_lost_packets(self, lost_packets_list):
        """
        handle messages we didn't handle yet.\n
        :param lost_packets_list: messages we got but never read them.
        """
        for packet in lost_packets_list:
            self.get_data_from_socket(packet)
        if len(lost_packets_list) == 0 and self.network.get_id() != DataManager.SERVER_ID:
            self.network.send(Ping().full_msg_with_header())

    def set_and_actions(self):
        """
        Create the GUI widgets.
        """
        self._canvas.grid_anchor('n')

        self.scBar = ttk.Scrollbar(self._canvas, orient=tk.VERTICAL, command=self._canvas.yview)
        self.scBar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.configure(yscrollcommand=self.scBar.set, background="#673ab7")
        self._canvas.bind('<Configure>', lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        self.frame_scroll = tk.Frame(self._canvas, bg="#673ab7")
        self.frame_scroll.pack(fill=tk.BOTH, expand=1)

        self._canvas.create_window((55, 10), window=self.frame_scroll, anchor="nw")

    def show_num_of_players(self):
        """
        Show the title widget that responsible to present the number of players.
        """
        self.label_num_of_player = tk.Label(self.frame_scroll, text=f"Number Of Players: {self.num_of_player}",
                                            borderwidth=0, relief="solid", bg="#673ab7", fg="black",
                                            font=("David bold", 20))
        self.label_num_of_player.grid(row=0, column=0, sticky='s', columnspan=2, pady=(0, 0))

    def show_player(self, player_index):
        """
        Show the player details name and avatar
        """
        color_bg = '#00cc66' if self.users_list[player_index].client_id == self.network.get_id() else '#673ab7'
        name_lbl = tk.Label(self.frame_scroll, text=f"{self.users_list[player_index].client_name}", borderwidth=2, relief="raised",
                 bg=color_bg, fg='white', font=("David bold", 15))
        name_lbl.grid(row=player_index + 1, column=0, sticky='w', pady=(5, 5))

        avatar_index = self.users_list[player_index].avatar_index
        current_avatar = ImageTk.PhotoImage(Image.open(DataManager.AVATAR_LIST[avatar_index]).resize((55, 85)),
                                            master=self.root)
        self.avatars_list.append(current_avatar)
        pic_lbl = tk.Label(self.frame_scroll, image=current_avatar, bg="#673ab7", width=45, height=80)
        pic_lbl.grid(row=player_index + 1, column=1, sticky='e', pady=(5, 5))
        user_view_data = (name_lbl,pic_lbl,self.users_list[player_index].client_id)
        self.users_labels[self.users_list[player_index]] = user_view_data


class GamePage(PageView, SocketCallBack):

    def __init__(self, root: PageViewManager, page_size, clients_data=None,title = None):
        """
        the Game Page.\n

        :param root: the window master (type:TK).
        :param clients_data: the players info
        :param title: window title.
        """
        self.network = root.get_network()
        self.frame_doll = None
        self.frame_board = None
        self.img_frame_doll = None
        self.lbl_frame_doll = None
        self.img_frame_board = None
        self.lbl_frame_board = None
        self.current_player = None
        self.img_doll = None
        self.lbl_doll = None

        self.is_allowed_to_move = True
        self.is_moving = False
        self.is_alive = True

        self.frame_doll_ratio = 0.28
        self.frame_board_ratio = 0.72

        self.images = []
        self.clients_data = clients_data if clients_data is not None else []

        self.players = []
        self.lose_players = []
        self.win_players = []
        self.identifier_name = title
        if title is None:
            title = f"Game Page - Player {self.network.get_id()}" if isinstance(self.network,
                                                                            Client) else f"Game Page - Server"
        else:
            title = f"Game Page - {title}"

        super().__init__(root, page_size=page_size, title=title, img_background_name="back_waiting.png")

        self.network.set_socket_call_back(self)
        lost_packets_list = self.root.get_lost_packets_list()
        self.root.clear_lost_packets_list()
        self.handle_lost_packets(lost_packets_list)

    def handle_lost_packets(self, lost_packets_list):
        """
        handle messages we didn't handle yet.\n
        :param lost_packets_list: messages we got but never read them.
        """
        for packet in lost_packets_list:
            self.get_data_from_socket(packet)

    def set_and_actions(self):
        """
        Create the GUI widgets.
        """
        if len(self.clients_data) == 0:
            self.socket_error("didn't got players")
        self._canvas.grid_anchor('n')
        self.resize_window(500, 500)

    def resize_window(self, width, height):
        """
        change widgets size and place in case the window size changed.\n
        present all the widget on the window.

        :param width: window width
        :param height: window height
        """
        is_first_step = True
        if self.frame_doll is not None and self.frame_board is not None:
            self.frame_doll.grid_forget()
            self.frame_board.grid_forget()
            is_first_step = False

        doll_height = int(height * self.frame_doll_ratio) if int(height * self.frame_doll_ratio) > 0 else 1
        board_height = int(height * self.frame_board_ratio) if int(height * self.frame_board_ratio) > 0 else 1
        width = width if width > 0 else 1

        self.frame_doll = tk.Frame(self._canvas)
        self.frame_doll.grid(row=0, column=0, sticky='n')

        self.frame_board = tk.Frame(self._canvas)
        self.frame_board.grid(row=1, column=0)

        self.img_frame_doll = ImageTk.PhotoImage(Image.open("game_doll.png").resize((width, doll_height)),
                                                 master=self.root)  # ratio: 0.28 (140/500)
        self.lbl_frame_doll = tk.Label(self.frame_doll, image=self.img_frame_doll, bg="red", width=width,
                                       height=0 if doll_height < 2 else doll_height - 2)
        self.lbl_frame_doll.grid(row=0, column=0, rowspan=1000, columnspan=1000)

        img_doll = ImageTk.PhotoImage(Image.open("doll_back.png").resize(
            (1 if width // 5 < 6 else width // 5 - 5, 1 if doll_height < 6 else doll_height - 5)), master=self.root)
        self.images.append(img_doll)
        self.lbl_doll = tk.Label(self.frame_doll, image=img_doll, bg="red",
                                 width=1 if width // 5 < 11 else width // 5 - 10,
                                 height=1 if doll_height < 11 else doll_height - 10)
        self.lbl_doll.place(x=width // 2 - width // 10, y=3)

        self.img_frame_board = ImageTk.PhotoImage(Image.open("game_board.png").resize((width, board_height)),
                                                  master=self.root)
        self.lbl_frame_board = tk.Label(self.frame_board, image=self.img_frame_board,
                                        height=0 if board_height < 2 else board_height - 2)
        self.lbl_frame_board.grid(row=0, column=0, rowspan=1000, columnspan=1000)

        self.doll_height = doll_height
        self.board_height = board_height
        self.width = width

        if is_first_step:
            for player_data in self.clients_data:
                self.players.append(Player(self.root, \
                                           self.frame_board, \
                                           avatar_index=player_data.avatar_index, \
                                           width=width, \
                                           height=board_height, \
                                           is_pc_player=player_data.is_pc_player, \
                                           id=player_data.client_id, \
                                           is_current=player_data.client_id == self.network.get_id(), \
                                           name=player_data.client_name, \
                                           num_of_players=len(self.clients_data)))
                if player_data.client_id == self.network.get_id():
                    self.current_player = self.players[len(self.players) - 1]

        else:

            for player in self.players:
                player.show_player(self.frame_board, width, board_height, num_of_players=len(self.players))

            for player in self.win_players:
                player.show_winner_player(self.frame_doll, self.width, self.board_height,
                                       doll_height=self.doll_height)

    def player_status(self, player_status_msg):
        """
        Handles the case that we got a 'PlayerMovingStatus' message.\n
        move the player on the board.\n
        verify if the player finish the board steps.\n

        :param player_status_msg: PlayerMovingStatus message.
        """
        win_player = None
        for player in self.players:
            if player.id == player_status_msg.player_id:
                player.is_moving = player_status_msg.is_moving
                if player_status_msg.is_moving and player.y <= DataManager.GAME_STEPS - 1:
                    player.move()
                    player.show_player(self.frame_board, self.width, self.board_height,
                                       num_of_players=len(self.players),is_forgot=False)
                elif player.y >= DataManager.GAME_STEPS:
                    win_player = player
                    player.lbl.place_forget()
                    self.win_players.append(player)
                    player.show_winner_player(self.frame_doll, self.width, self.board_height,
                                       doll_height=self.doll_height, winner_place=len(self.win_players) - 1)
        if win_player is not None:
            self.players.remove(win_player)
            if win_player.id == self.network.get_id():
                self.is_alive = False
                self.is_allowed_to_move = False
                self.is_moving = False

    def turn_doll_img(self, img_name):
        """
        set doll img.

        :param img_name: doll img (front or back).
        """
        img_doll = ImageTk.PhotoImage(Image.open(img_name).resize(
            (self.images[len(self.images) - 1].width(), self.images[len(self.images) - 1].height())), master=self.root)
        self.images.append(img_doll)
        self.lbl_doll.configure(image=img_doll)

    def kill_player(self, player_id):
        """
        in case a player exit from the game or lost -> remove him from board.\n

        :param player_id: the player we need to remove from board.
        """
        is_find = False
        for player in self.players:
            if player.id == player_id:
                player.kill()
                self.lose_players.append(player)
                is_find = True
        if is_find:
            self.players.remove(self.lose_players[len(self.lose_players) - 1])

    def forget_lose_players(self):
        """
        execute lose players forget -> will erase the player img from board.
        """
        for player in self.lose_players:
            player.forget()


class Player:
    def __init__(self, root, parent, avatar_index=0, bg='#f6cf8c', width=50, height=50, id=0, num_of_players=1,
                 is_moving=False, is_pc_player=False, is_current=False, name=""):
        """
        manage the player GUI widgets.

        :param root: the window root (TK)
        :param parent: the widget the player inside him.
        :param avatar_index: the avatar img index.
        :param bg: player color.
        :param width: window current width size.
        :param height: window current height size.
        :param id: client id
        :param num_of_players: num of players in the game.
        :param is_moving: is player moving or not
        :param name: player name
        """
        self.x = width // 2
        self.y = 1
        self.img = None
        self.lbl = None
        self.place = None
        self.bg = bg
        self.avatar_index = avatar_index
        self.root = root
        self.id = id
        self.is_moving = is_moving
        self.is_pc_player = is_pc_player
        self.is_current = is_current
        self.name = name

        self.game_steps = DataManager.GAME_STEPS

        self.width_divider = 12

        self.show_player(parent, width=width, height=height, num_of_players=num_of_players)

    def show_player(self, parent, width=50, height=50, num_of_players=1,is_forgot=True):
        """
        will show player GUI widget on the window
        """
        lock = threading.Lock()
        lock.acquire()

        # defined size
        height_parse = self.calculate_height(height)
        width_parse = self.calculate_width(width)
        if is_forgot:
            self.img = ImageTk.PhotoImage(
                Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((width_parse, height_parse)),
                master=self.root)

            self.bg = "green" if self.is_current else self.bg
            self.lbl = tk.Label(parent, image=self.img, bg=self.bg, borderwidth=1.5, relief="groove",
                                width=width_parse, height=height_parse)

        # define place
        y_parse = self.calculate_y(height - height_parse)
        x_parse = self.calculate_x(width, width_parse, num_of_players)

        self.lbl.place(x=x_parse, y=y_parse)
        lock.release()

    def show_winner_player(self, parent, width=50, height=50, doll_height=50, winner_place=None):
        """
        will show players GUI widget on the winners frame.
        """
        lock = threading.Lock()
        lock.acquire()

        self.place = self.place if winner_place is None else winner_place
        # defined size
        height_parse = self.calculate_height(height)
        width_parse = self.calculate_width(width)

        self.img = ImageTk.PhotoImage(
            Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((width_parse, height_parse)),
            master=self.root)
        self.bg = "green" if self.is_current else self.bg
        self.lbl = tk.Label(parent, image=self.img, bg=self.bg, borderwidth=1.5, relief="groove",
                            width=width_parse, height=height_parse)

        # define placeGrid
        self.lbl.place(x=width_parse*self.place, y=doll_height-height_parse-5 if doll_height-height_parse-5 > 0 else 1 )

        lock.release()

    def move(self, y=1):
        """
        set player moving

        :param y: how many steps to move.
        """
        if self.is_pc_player:
            self.y += y*2.5
        else:
            self.y += y

    def kill(self):
        """
        erase player img.
        """
        self.img = ImageTk.PhotoImage(
            Image.open("lost_image.png").resize((self.img.width(), self.img.height())),
            master=self.root)
        self.lbl.config(image=self.img)

    def forget(self):
        """
        erase player lbl.
        """
        self.lbl.place_forget()

    def calculate_height(self, height):
        size_h = int((height // self.game_steps) + height * 0.17)
        return size_h if size_h > 0 else 1

    def calculate_width(self, width):
        size_w = width // self.width_divider
        return size_w if size_w > 0 else 1

    def calculate_y(self, height):
        return height - (self.y * height // self.game_steps)

    def calculate_x(self, width, width_parse, num_of_players):
        padding = self.id * 0.1 * width
        be_in_center = (width - (num_of_players * width_parse)) / 2
        return int(be_in_center + padding)


class ErrorPage(PageView):

    def __init__(self, root: PageViewManager, page_size, error=None):
        """
        responsible to show a error.

        :param root: window root.
        :param page_size: window.
        :param error: error msg.
        """
        super().__init__(root, page_size=page_size, title="EXIT", img_background_name="error_back.png")
        self._canvas.grid_anchor('center')
        if error is None:
            error="Error!"

        self.lbl_submit = tk.Label(self._canvas, text=error, borderwidth=0,
                                       relief="solid", bg='#0078d7', fg="white", font=("David bold", 20))
        self.lbl_submit.grid(row=0, column=0,sticky='n', pady=(150, 5))


if __name__ == "__main__":
    """
        Program should run from main.py for the correct flow
        all class here are abstract and uses in client and server pages
    """
    pass
