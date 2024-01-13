from client_server import Server
from page_view_manager import PageViewManager, PAGE_TYPES

if __name__ == "__main__":
    server = Server()
    pageViewManager = PageViewManager(network=server)
    pageViewManager.display_screen(PAGE_TYPES.SERVER_PLAYERS_AMOUNT)
    pageViewManager.kill_all()