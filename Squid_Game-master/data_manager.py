from enum import Enum
import json


class DataMessage:
    def __init__(self, json_msg=None):
        """
        used as abstract class for json messages between Clients & Server.\n
        in the constructor if json_msg is not None we parsing the json to variables.\n

        :param json_msg: a json data
        """
        if json_msg is not None:
            self.__dict__ = json.loads(json_msg)

    def to_json(self):
        """
        Parsing class variables to json.
        """
        return json.dumps(self, default=lambda o: o.__dict__)

    def full_msg_with_header(self):
        """
        Parsing class variables to json and add the message header.
        """
        for header, context in DataManager.MSG_TYPES.items():
            if isinstance(self, context):
                return header + self.to_json() + DataManager.SPLIT_MESSAGES


class ClientRegisteredMessage(DataMessage):
    def __init__(self, json_msg=None, client_name=None, client_id=None, avatar_index=0, is_pc_player=False):
        """
        Json msg class, will send when Client finish to register.\n

        :param client_name: client_name.
        :param client_id: client_id.
        :param avatar_index: avatar_index.
        :param is_pc_player: is_pc_player.
        """
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.client_name = client_name
            self.client_id = client_id
            self.avatar_index = avatar_index
            self.is_pc_player = is_pc_player


class NumOFPlayersMessage(DataMessage):
    """
    Json msg class, Send how many players in the game (server will send).\n
    """
    def __init__(self, json_msg=None, num_of_players=0):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.num_of_players = num_of_players


class ListenOk(DataMessage):
    """
    Json msg class, clients sends they listen to server.\n
    """
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class StartGame(DataMessage):
    """
    Json msg class, Server send in case he want to start the game.\n
    """
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class PlayerMovingStatus(DataMessage):
    """
    Json msg class, Clients sends in case it want to tell server he move in the game.\n
    """
    def __init__(self, json_msg=None, player_id=None, is_moving=False):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.player_id = player_id
            self.is_moving = is_moving


class DollGonnaTurning(DataMessage):
    """
    Json msg class, Server send in case it want tell to client the doll gonna turning.\n
    """
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class DollTurned(DataMessage):
    """
    Json msg class, Server send in case it want to client the doll gonna turning.\n
    """
    def __init__(self, json_msg=None, is_front=False):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.is_front = is_front


class PlayerFinishedHandleDollTurning(DataMessage):
    """
    Json msg class, Client send in case it want to tell Server he stop handle doll turning.\n
    """
    def __init__(self, json_msg=None, is_lose=False, id=0):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.is_lose = is_lose
            self.id = id


class PlayerLose(DataMessage):
    """
    Json msg class, Sending the id of the loser client.\n
    """
    def __init__(self, json_msg=None, id=None):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.id = id


class CloseConnection(DataMessage):
    """
    Json msg class, Clients Sending Server they close connection.\n
    """
    def __init__(self, json_msg=None, id=0):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.id = id


class GameFinished(DataMessage):
    """
    Json msg class, Server Sending Clients the game finished.\n
    """
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class KillAll(DataMessage):
    """
    Json msg class, Server Sending Clients to terminate themselves.\n
    """
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class Ping(DataMessage):
    def __init__(self, json_msg=None):
        super().__init__(json_msg=json_msg)


class PlayerName(DataMessage):
    """
    Json msg class, Clients send to tell other clients there name.\n
    """
    def __init__(self, json_msg=None, name=None):
        super().__init__(json_msg=json_msg)
        if json_msg is None:
            self.name = name


class DataManager:
    def __init__(self):
        """
        an static class that contain game const data.
        """
        pass

    NUM_OF_MAX_CLIENTS = 5
    MSG_TYPES = {
        "0000": ClientRegisteredMessage,
        "0001": NumOFPlayersMessage,
        "0002": ListenOk,
        "0003": PlayerMovingStatus,
        "0004": StartGame,
        "0005": DollGonnaTurning,
        "0006": DollTurned,
        "0007": PlayerFinishedHandleDollTurning,
        "0008": PlayerLose,
        "0009": CloseConnection,
        "0010": GameFinished,
        "0011": KillAll,
        "0012": Ping,
        "0013": PlayerName

    }
    SERVER_ID = -1
    CLOSE_CONNECTION = "0009{"
    MSG_HEADER_SIZE = 4
    GAME_STEPS = 100
    NAME_STRING_LIMIT = 20
    LOG_FILE_NAME = "games.log"
    LOG_START_NAME = f"GAME:{'-' * 20}"
    LOG_START_WINNERS = f"WINNERS{'-' * 20}"
    LOG_START_LOSERS = f"LOSERS:{'-' * 20}"
    SPLIT_MESSAGES = "SPLIT_MESSAGE"
    AVATAR_LIST = ["avatars/avatar_67.png", \
                   "avatars/avatar_master.png", \
                   "avatars/avatar_square.png", \
                   "avatars/avatar_001_ver_2.png", \
                   "avatars/avatar_rectangle.png", \
                   "avatars/avatar_67_ver_2.png", \
                   "avatars/avatar_199.png", \
                   "avatars/avatar_001.png", \
                   "avatars/avatar_218.png", \
                   "avatars/avatar_218.png", \
                   "avatars/avatar_456.png"]


if __name__ == "__main__":
    """
          This Module contain all the program const Data & Messages.
          
          Program should run from main.py for the correct flow.
    """
    pass
