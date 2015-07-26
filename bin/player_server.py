#!/usr/bin/python3

import logging

from pygdl.gamestate import GameState
from pygdl.players import LegalGamePlayer
from pygdl.playerserver import run_player_server

logging.basicConfig(level=logging.DEBUG)

run_player_server(LegalGamePlayer, GameState)
