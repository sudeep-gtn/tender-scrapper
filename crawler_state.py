# crawler_state.py
from threading import Lock

class CrawlerState:
    def __init__(self):
        self.lock = Lock()
        self.running = False
        self.results = []

state = CrawlerState()