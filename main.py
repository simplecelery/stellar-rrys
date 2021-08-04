import os
import sys
import StellarPlayer
import threading
import time
import random
import requests
from bs4 import BeautifulSoup

from .simple import PluginImpl


class Plugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self, player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.pi = PluginImpl(player)
  
    def show(self):
        thread = threading.Thread(target=self.pi.show, args=(), daemon=True)
        thread.start()

    
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    return Plugin(player)

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()

