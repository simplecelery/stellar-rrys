import os
import sys
import StellarPlayer
import threading
import time
import random
import requests

from .simple import PluginImpl


class Plugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self, player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.pi = PluginImpl(player)
        thread = threading.Thread(target=self.pi.show_thread, args=(), daemon=True)
        thread.start()
  
    def show(self):
        self.pi.show_flag = True

    def close(self):
        self.pi.show_flag = False


def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    return Plugin(player)


def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()

