import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image
import random

from PIL.Image import Resampling

from page_view_manager import PageViewManager, PageView, PAGE_TYPES, GamePage, ErrorPage
from data_manager import DataManager, ClientRegisteredMessage, ListenOk, PlayerMovingStatus, DollGonnaTurning, \
    DollTurned, PlayerFinishedHandleDollTurning, PlayerLose, CloseConnection, GameFinished, KillAll, Ping, PlayerName, \
    StartGame
from client_server import SocketCallBack, Server, Client


class ClientRegister(PageView, SocketCallBack):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is KillAll:
            self.is_error_occurred = True
            self.destroy()
            self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

        elif DataManager.MSG_TYPES[header] is PlayerName:
            self.other_players_names.append(DataManager.MSG_TYPES[header](json_msg=context).name)

        #save packets for next pages
        else:
            self.root.add_lost_packet(data)

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error = "Server is Closed or never Opened")

    def __init__(self, root: PageViewManager, page_size):
        """
        clients registration page.

        :param root: window root.
        :param page_size: window size.
        """
        self.entry_name = None
        self.label_add_name = None
        self.label_description = None
        self.button_submit = None
        self.button_pc_player = None
        self.current_avatar = None
        self.avatar_window = None
        self.label_chose_avatar = None
        self.button_back = None
        self.button_next = None
        self.label_error = None
        self.avatar_index = 0
        self.other_players_names = []
        self.network = root.get_network()
        super().__init__(root, page_size=page_size, title='Player Registration',
                         img_background_name='back_register.png')

        self.network.set_socket_call_back(self)
        self.network.connect_to_network()
        self.network.start_getting_data_thread()
        self.network.send(ListenOk().full_msg_with_header())

    def set_and_actions(self):
        """
        Create the GUI widgets.
        """
        self._canvas.grid_anchor('center')

        self.label_description = tk.Label(self._canvas, text="Registration", borderwidth=0, relief="solid",
                                          bg='#f4d056', fg="black", font=("David bold", 20))
        self.label_description.grid(row=0, column=0, sticky='s', columnspan=2)

        self.label_add_name = tk.Label(self._canvas, text="Enter your name:", borderwidth=0, relief="solid",
                                       bg='#f4d056', fg="black", font=("David bold", 13))
        self.label_add_name.grid(row=1, column=0, sticky='w', pady=(15, 25))

        self.entry_name = tk.Entry(self._canvas, highlightthickness=1)
        self.entry_name.config(highlightbackground="black", highlightcolor="black")
        self.entry_name.grid(row=1, column=1, sticky='e', pady=(15, 25), padx=5)

        self.label_chose_avatar = tk.Label(self._canvas, text="Choose an avatar:", borderwidth=0, relief="solid",
                                           bg='#f4d056', fg="black", font=("David bold", 13))
        self.label_chose_avatar.grid(row=2, column=0, sticky='w', pady=(0, 20))

        self.current_avatar = ImageTk.PhotoImage(
            Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((95, 179)), master=self.root)
        self.avatar_window = tk.Label(self._canvas, image=self.current_avatar, bg='#f4d056', width=90, height=175)
        self.avatar_window.grid(row=3, column=0, columnspan=2)

        self.button_back = tk.Button(self._canvas, text="<<", command=self.__back_button_action, borderwidth=3,
                                     relief="raised", bg='#f4d056', fg="black", font=("David bold", 13))
        self.button_back.grid(row=4, column=0, sticky='w')

        self.button_next = tk.Button(self._canvas, text=">>", command=self.__next_button_action, borderwidth=3,
                                     relief="raised", bg='#f4d056', fg="black", font=("David bold", 13))
        self.button_next.grid(row=4, column=3, sticky='w')

        self.button_submit = tk.Button(self._canvas, text="Submit", command=self.__submit_action, borderwidth=3,
                                       relief="raised", bg='#f4d056', fg="black", font=("David bold", 13))
        self.button_submit.grid(row=5, column=0, sticky='w', pady=(20, 15))

        self.button_pc_player = tk.Button(self._canvas, text="PC Player", command=self.__pc_player_action,
                                          borderwidth=3, relief="raised", bg='#f4d056', fg="black",
                                          font=("David bold", 13))
        self.button_pc_player.grid(row=5, column=0, sticky='w', pady=(20, 15), padx=(80, 0))

        self.label_error = tk.Label(self._canvas, text="", borderwidth=0, relief="solid", bg='#f4d056', fg="red",
                                    font=("David bold", 13))

    def __next_button_action(self):
        """
        change the avatar widget to the next avatar img.
        """
        self.label_error.grid_forget()

        if len(DataManager.AVATAR_LIST) <= 1:
            return
        self.avatar_window.grid_forget()

        self.avatar_index += 1

        self.avatar_index = self.avatar_index if self.avatar_index < len(DataManager.AVATAR_LIST) else 0
        self.current_avatar = ImageTk.PhotoImage(
            Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((95, 179)), master=self.root)

        self.avatar_window = tk.Label(self._canvas, image=self.current_avatar, bg='#f4d056', width=90, height=175)
        self.avatar_window.grid(row=3, column=0, columnspan=2)

    def __back_button_action(self):
        """
        change the avatar widget to the previous avatar img.
        """
        self.label_error.grid_forget()

        if len(DataManager.AVATAR_LIST) <= 1:
            return
        self.avatar_window.grid_forget()

        self.avatar_index -= 1

        self.avatar_index = self.avatar_index if self.avatar_index >= 0 else len(DataManager.AVATAR_LIST) - 1

        self.current_avatar = ImageTk.PhotoImage(
            Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((95, 179)), master=self.root)

        self.avatar_window = tk.Label(self._canvas, image=self.current_avatar, bg='#f4d056', width=90, height=175)
        self.avatar_window.grid(row=3, column=0, columnspan=2)

    def __submit_action(self):
        """
        make registration in case the submit btn clicked and all data correct.
        """
        self.label_error.grid_forget()
        if self.entry_name.get() == "" or self.entry_name.get() is None:
            self.label_error.config(text="name cannot be empty!")
            self.label_error.grid(row=6, column=0, sticky='w', pady=(0, 20))
            return
        if len(self.entry_name.get()) > DataManager.NAME_STRING_LIMIT:
            self.label_error.config(text=f"name cannot be greater then {DataManager.NAME_STRING_LIMIT}!")
            self.label_error.grid(row=6, column=0, sticky='w', pady=(0, 20))
            return
        if self.entry_name.get() in self.other_players_names:
            self.label_error.config(text=f"This name already taken!")
            self.label_error.grid(row=6, column=0, sticky='w', pady=(0, 20))
            return

        self.__finish_registration(is_pc_player=False)

    def __pc_player_action(self):
        """
        in case the pc player clicked get a random name & avatar, and continue the next page.
        """
        self.label_error.grid_forget()

        self.entry_name.delete(0, 'end')
        self.entry_name.insert(0, f"PC")

        self.avatar_window.grid_forget()
        self.avatar_index = random.randint(0, len(DataManager.AVATAR_LIST) - 1)
        self.current_avatar = ImageTk.PhotoImage(
            Image.open(DataManager.AVATAR_LIST[self.avatar_index]).resize((95, 179)), master=self.root)
        self.avatar_window = tk.Label(self._canvas, image=self.current_avatar, width=90, height=175)
        self.avatar_window.grid(row=3, column=0, columnspan=2)

        self.__finish_registration(is_pc_player=True)

    def __finish_registration(self, is_pc_player=False):
        """
        in case all data ok.\n
        send to server ClientRegisteredMessage data.\n
        move to the next page.\n

        :param is_pc_player: get if it's a pc player
        """
        register_details = ClientRegisteredMessage(client_name=self.entry_name.get(), client_id=self.network.get_id(),
                                                   avatar_index=self.avatar_index, is_pc_player=is_pc_player)

        self.network.send(register_details.full_msg_with_header())
        self.network.send(PlayerName(name=self.entry_name.get()).full_msg_with_header())
        self.root.change_display_screen(PAGE_TYPES.CLIENT_WAITING_PAGE, title =f"{self.entry_name.get()}")


class ClientGamePage(GamePage):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is KillAll:
            self.is_error_occurred = True
            self.destroy()
            self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

        elif DataManager.MSG_TYPES[header] is PlayerMovingStatus:
            self.player_status(DataManager.MSG_TYPES[header](json_msg=context))

        elif DataManager.MSG_TYPES[header] is DollGonnaTurning:
            if not self.current_player.is_pc_player:
                self.is_doll_gonna_turn = True
                self.gonna_turn_light_img("red_circle_s.png")

        elif DataManager.MSG_TYPES[header] is PlayerLose:
            player_lose = DataManager.MSG_TYPES[header](json_msg=context)
            self.kill_player(player_lose.id)
            if player_lose.id == self.network.get_id():
                self.client_lose()

        elif DataManager.MSG_TYPES[header] is DollTurned:
            doll_status = DataManager.MSG_TYPES[header](json_msg=context)
            if not doll_status.is_front:
                self.turn_doll_img("doll_back.png")
                self.is_allowed_to_move = True
                self.forget_lose_players()
                if not self.current_player.is_pc_player:
                    self.is_doll_gonna_turn = False
                    self.gonna_turn_light_img("green_circle_s.png")

            else:
                self.turn_doll_img("doll_front.png")
                is_need_to_be_killed = self.is_moving and self.current_player.y < DataManager.GAME_STEPS-1
                if self.current_player.is_pc_player:
                    self.is_moving = False
                    self.is_allowed_to_move = False

                elif self.is_moving:
                    self.button_move_action()
                    self.is_allowed_to_move = False

                if is_need_to_be_killed and self.current_player.place is None:
                    if self.current_player.is_pc_player and self.current_player.y / DataManager.GAME_STEPS < 0.8:
                        self.network.send(PlayerFinishedHandleDollTurning().full_msg_with_header())
                    else:
                        self.network.send(
                            PlayerFinishedHandleDollTurning(id=self.network.get_id(), is_lose=True).full_msg_with_header())
                else:
                    self.network.send(PlayerFinishedHandleDollTurning().full_msg_with_header())

        elif DataManager.MSG_TYPES[header] is GameFinished:
            self.root.change_display_screen(PAGE_TYPES.CLIENT_GAME_FINISHED_PAGE,title=self.identifier_name ,lose_players_lst=self.lose_players, winner_players_lst=self.win_players)

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error = "Server is Closed or never Opened")

    def __init__(self, root: PageViewManager, page_size, clients_data=None,title=None):
        """
        the Client Game Page.\n

        :param root: the window master (type:TK).
        :param clients_data: players info.
        :param title: window title.
        """
        self.button_move = None
        self.light_img = None
        self.button_light = None
        self.is_doll_gonna_turn = False
        super().__init__(root, page_size=page_size, clients_data=clients_data, title=title)

    def move(self):
        """
        will execute in case it's not a pc player - > sending moving message.\n
        is moving will be false in case the stop btn cliecked.
        """
        while self.is_moving:
            self.network.send(
                PlayerMovingStatus(player_id=self.network.get_id(), is_moving=True).full_msg_with_header())
            time.sleep(0.3)

    def resize_window(self, width, height):
        """
        change widgets size and place in case the window size changed.\n
        present all the widget on the window.

        :param width: window width
        :param height: window height
        """
        super().resize_window(width, height)
        if not self.current_player.is_pc_player:
            text = "Stop" if self.is_moving else "Move"
            bg = "red" if self.is_moving else "green"
            self.button_move = tk.Button(self.frame_board, text=text, command=self.button_move_action, borderwidth=3,
                                         relief="raised", bg=bg, fg="black", font=("David bold", 13))
            self.button_move.grid(row=5, column=0, sticky='sw', pady=(20, 15), padx=(20, 20))

            img_name = "red_circle_s.png" if self.is_doll_gonna_turn else "green_circle_s.png"
            self.light_img = tk.PhotoImage(file=img_name, master=self.root)
            self.button_light = tk.Button(self.frame_board, image=self.light_img, borderwidth=0, width=70, height=70)
            self.button_light.grid(row=5, column=0, sticky='se', pady=(20, 15),
                                   padx=(width - 80 if width - 80 > 0 else 1, 20))

    def set_and_actions(self):
        """
        Create the GUI widgets.
        """
        super().set_and_actions()
        if self.current_player.is_pc_player:
            th = threading.Thread(target=self.pc_player_move)
            th.daemon=True
            th.start()

    def button_move_action(self):
        """
        In case the 'Stop & move' btn clicked, recognize if we are in state 'stop' or 'move'.\n
        in case we change from 'Stop' to 'Move' - start the moving thread until the btn move to stop.\n
        in case we change from 'Move' to 'Stop' - stop the moving and send server we stop.\n
        (not for pc players).\n
        """
        if self.is_allowed_to_move is False:
            return
        self.is_moving = not self.is_moving
        if self.is_moving:
            th = threading.Thread(target=self.move)
            th.daemon=True
            th.start()
            self.button_move.configure(text="Stop", bg="red")
        else:
            self.network.send(
                PlayerMovingStatus(player_id=self.network.get_id(), is_moving=False).full_msg_with_header())
            self.button_move.configure(text="Move", bg="green")

    def pc_player_move(self):
        """
        manage the pc player moving & stopping thread.
        """
        self.is_need_to_send_stop = False
        time.sleep(1)
        while self.is_alive:
            rand_num = random.randint(0, 10)
            self.is_moving = rand_num > 5
            if self.is_moving and self.is_allowed_to_move:
                self.network.send(
                    PlayerMovingStatus(player_id=self.network.get_id(), is_moving=True).full_msg_with_header())
                time.sleep(0.3)
                self.is_need_to_send_stop = True

            elif not self.is_moving and self.is_need_to_send_stop:
                self.network.send(
                    PlayerMovingStatus(player_id=self.network.get_id(), is_moving=False).full_msg_with_header())
                self.is_need_to_send_stop = False
                time.sleep(1)

            else:
                time.sleep(0.3)

    def gonna_turn_light_img(self, img_name):
        """
        set the circle img indication.\n

        :param img_name: red or green circle image (give indication if the doll gonna turn.)
        """
        self.light_img = tk.PhotoImage(file=img_name, master=self.root)
        self.button_light.configure(image=self.light_img)

    def client_lose(self):
        """
        execute in case the specific player lose.\n
        will close threads.\n
        close network.\n
        move to the client lose page.\n
        """
        self.close_all_threads()
        self.root.change_display_screen(PAGE_TYPES.CLIENT_LOST_PAGE)
        self.network.close()

    def close_all_threads(self):
        """
        closing threads keys.\n
        """
        self.network.set_socket_call_back(None)
        self.is_alive = False
        self.is_allowed_to_move = False
        self.is_moving = False


class ClientLostPage(PageView):
    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is KillAll:
            self.is_error_occurred = True
            self.destroy()
            self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

    def socket_error(self, error_msg):
        """
        Handle socket error.
        """
        if self.is_error_occurred:
            return
        self.is_error_occurred = True
        self.destroy()
        self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

    def __init__(self, root: PageViewManager, page_size, clients_data=None):
        """
        the lost page tell the user he lost and exit the window automatically after 3.5 seconds.\n

        :param root: window root.
        :param page_size: window size
        """
        super().__init__(root, page_size=page_size, title="lost", img_background_name="lost_back.png")
        self._canvas.grid_anchor('center')
        self.lbl_submit = tk.Button(self._canvas, text="You Lose! by!", borderwidth=2,
                                       relief="solid", bg='#FF337D', fg="white", font=("David bold", 26))
        self.lbl_submit.grid(row=0, column=0,sticky='s', pady=(150, 5))
        threading.Thread(target=self.finish).start()

    def finish(self):
        """
        destroy the window after 3.5 seconds.
        """
        time.sleep(3.5)
        self.root.destroy()


class ClientGameFinishedPage(PageView, SocketCallBack):

    def get_data_from_socket(self, data):
        """
        Callback interface for getting server & client messages.\n
        parsing the msg and handle it.
        """
        header, context = (data[0:DataManager.MSG_HEADER_SIZE], data[DataManager.MSG_HEADER_SIZE:])
        if DataManager.MSG_TYPES[header] is KillAll:
            self.is_error_occurred = True
            self.destroy()
            self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

        elif DataManager.MSG_TYPES[header] is StartGame:
            players_in_game = list(map(
                lambda player: ClientRegisteredMessage(client_name=player.name, client_id=player.id,
                                                       avatar_index=player.avatar_index,
                                                       is_pc_player=player.is_pc_player), self.alive_clients))
            self.root.change_display_screen(PAGE_TYPES.CLIENT_GAME_PAGE, clients_data=players_in_game, title=f"{self.identifier_name}")

        elif DataManager.MSG_TYPES[header] is CloseConnection:
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
        self.root.change_display_screen(PAGE_TYPES.CLIENT_ERROR_PAGE, error="Server is Closed or never Opened")

    def __init__(self, root: PageViewManager, page_size, title = None, lose_players_lst=None, winner_players_lst=None):
        """
        this page showing the game result.

        :param root: window root.
        :param page_size: window size.
        :param title: window title.
        :param lose_players_lst: The losers data.
        :param winner_players_lst: The winners data.
        """
        self.lose_players_lst = lose_players_lst
        self.winner_players_lst = winner_players_lst
        self.alive_clients = winner_players_lst
        self.scBar = None
        self.frame_scroll = None
        self.network = root.get_network()
        self.identifier_name = title
        self.back_img = None
        self.lbl_img = None
        self.current_canvas = None
        self.identifier_name = title

        if title is None:
            title = "Results Page"
        else:
            title = f"Results Page - {title}"

        super().__init__(root, page_size=page_size, title=title, img_background_name="back_finished.png")

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
        self.network.send(Ping().full_msg_with_header())

    def set_and_actions(self,width=500,height=500):
        """
        Create the GUI widgets.
        """
        self.configure(background="#181617")

        self.frame_scroll = tk.Frame(self._canvas,background="#181617")
        self.frame_scroll.pack(fill=tk.BOTH, expand=1)

        self.scBar = ttk.Scrollbar(self._canvas, orient=tk.VERTICAL, command=self._canvas.yview)
        self.scBar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.configure(yscrollcommand=self.scBar.set, background="#181617")
        self._canvas.bind('<Configure>', lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        self.back_img = ImageTk.PhotoImage(Image.open("back_finished.png").resize((width, height)),master=self.root)
        self.lbl_img = tk.Label(self.frame_scroll, image=self.back_img,borderwidth=0,width=width, height=height, background="#181617")
        self.lbl_img.grid(row=0, column=0, sticky='nw',columnspan=9999, rowspan=9999)

        tk.Label(self.frame_scroll, text="Places:", borderwidth=2,
                                       relief="solid", bg='#181617', fg="white", font=("David bold", 26))\
                                        .grid(row=0, column=0, sticky='sw', padx=(15,0),pady=(height//7, height//20))

        self.show_players(width=width,height=height)

        self.current_canvas=self._canvas.create_window((0,0),window=self.frame_scroll, anchor="nw")

    def resize_window(self,width, height):
        """
        change widgets size and place in case the window size changed.\n
        present all the widget on the window.

        :param width: window width
        :param height: window height
        """
        self._canvas.delete(self.current_canvas)
        self.frame_scroll.forget()
        self.scBar.forget()
        self.set_and_actions(width, height)

    def show_players(self,width=500,height=500):
        """
        run on win players lst & lose players lst - and execute on each player 'show player' function.\n
        show players data on widgets (name, img, game's rate).\n

        :param width: window width.
        :param height: window height.
        """
        index=0
        if self.winner_players_lst is not None:
            for player in self.winner_players_lst:
                self.show_player(player,index,width=width,height=height)
                index += 1

        if self.lose_players_lst is not None:
            for player in self.lose_players_lst:
                self.show_player(player,index,width=width,height=height,is_winner = False)
                index += 1

    def show_player(self, player, index,width=500,height=500,is_winner = True):
        """
        show players data on widgets (name, img, game's rate).\n

        :param player: contain player data and widgets.
        :param index: grid row index.
        :param width: window width.
        :param height: window height.
        :param is_winner: help to separate between lose and winners.
        :return:
        """
        pady= 0
        color_bg = '#00cc66' if player.id == self.network.get_id() else '#181617'
        tk.Label(self.frame_scroll, text=f"{player.name}", borderwidth=2, relief="raised",
                 bg=color_bg, fg='white', font=("David bold", 15)) \
            .grid(row=index + 1, column=1, sticky='w', pady=(pady, 5),padx=(0,width//6))

        player.img = None
        avatar_index = player.avatar_index
        player.img = ImageTk.PhotoImage(Image.open(DataManager.AVATAR_LIST[avatar_index]).resize((55, 85)),master=self.root)

        tk.Label(self.frame_scroll, image=player.img, bg="#181617", width=45, height=80)\
        .grid(row=index + 1, column=2, sticky='sw', pady=(pady, 5),padx=(0,0))

        if is_winner:
            tk.Label(self.frame_scroll, text=f"{index+1}.", borderwidth=2,
                                       relief="solid", bg='#181617', fg="white", font=("David bold", 26))\
                                        .grid(row=index + 1, column=0, sticky='w', padx=(15,0),pady=(pady, 5))
        else:
            tk.Frame(self.frame_scroll, borderwidth=0,width=width//6+player.img.width()+175,height=5,bg='red')\
                                        .grid(row=index + 1,sticky='w', column=0, padx=(15,0),pady=(pady, 5),columnspan=width)


class ClientErrorPage(ErrorPage):

    def __init__(self, root: PageViewManager, page_size, error=None):
        """
        Will use in case an error occurred.\n
        The page show the client error and close the window automatically after 2 seconds.\n

        :param root: window root.
        :param page_size: window size.
        :param error: the error we want to present.
        """
        if error is not None:
            error+=", Bye!"
        super().__init__(root, page_size, error=error)
        threading.Thread(target=self.finish).start()

    def finish(self):
        """
        Will window the frame after 2 seconds
        """
        time.sleep(2)
        self.root.destroy()


if __name__ == "__main__":
    """
        Client Pages in case you want to debug:
            CLIENT_REGISTER
            CLIENT_WAITING_PAGE
            CLIENT_GAME_PAGE  
            CLIENT_LOST_PAGE
            CLIENT_GAME_FINISHED_PAGE
            CLIENT_ERROR_PAGE

        Simulating Error !!! Program should run from main.py for the correct flow
        Simulating Client to open without server operating, and expecting Error  
        Error page will close automatically after 2 seconds!!!!!!
    """
    pass








