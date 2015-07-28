#!/usr/bin/python3

import argparse
import logging

from pygdl.gamestate import KIFGameState
from pygdl.players import Legal, Random
from pygdl.playerserver import run_player_server

player_classes = [Legal, Random]
player_class_dict = {class_.__name__: class_
                     for class_ in player_classes}

class LogLevel(object):
    levels = ['debug', 'info', 'warning', 'error', 'critical']
    def __init__(self, level_string):
        if level_string in self.levels:
            self.level = getattr(logging, level_string.upper())
        else:
            self.level = int(level_string)

parser = argparse.ArgumentParser(description="General Game Player Server")
parser.add_argument('player', type=str,
                    choices=player_class_dict.keys(),
                    help="Game player class.")
parser.add_argument('-P', '--port', type=int, default=9147,
                    help="Port on which the server listens.")
parser.add_argument('--log-level', type=LogLevel, default='info',
                    help=("Set logging level. "
                          "Either an integer value or one of: "
                          "{} (default '{}')".format(LogLevel.levels,
                                                     'info')))
args = parser.parse_args()

logging.basicConfig(level=args.log_level.level)
run_player_server(player_class_dict[args.player], KIFGameState)
