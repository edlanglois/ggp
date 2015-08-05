#!/usr/bin/python3

import argparse
import inspect
import logging

from pygdl.gamestate import KIFGameState
from pygdl.players import (
    PlayerFactory,
    AlphaBeta,
    BoundedDepth,
    CompulsiveDeliberation,
    Legal,
    Minimax,
    Random,
    SequentialPlanner,
)
from pygdl.playerserver import run_player_server

player_classes = [
    Legal,
    AlphaBeta,
    BoundedDepth,
    CompulsiveDeliberation,
    Minimax,
    Random,
    SequentialPlanner,
]
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
parser.add_argument('-P', '--port', type=int, default=9147,
                    help="Port on which the server listens.")
parser.add_argument('--log-level', type=LogLevel, default='info',
                    help=("Set logging level. "
                          "Either an integer value or one of: "
                          "{} (default '{}')".format(
                              ', '.join(LogLevel.levels), 'info')))
subparsers = parser.add_subparsers(
    title='Players', dest='player', metavar='PLAYER',
    help='Game player class.')

for player in player_classes:
    player_parser = subparsers.add_parser(player.__name__,
                                          help=inspect.getdoc(player))
    for param_name, param_description in player.PARAMETER_DESCRIPTIONS.items():
        player_parser.add_argument(param_name, **param_description.dict)

args = parser.parse_args()

logging.basicConfig(level=args.log_level.level)
player_class = player_class_dict[args.player]
player_kwargs = {param_name: getattr(args, param_name)
                 for param_name in player_class.PARAMETER_DESCRIPTIONS.keys()}
player_factory = PlayerFactory(player_class, **player_kwargs)
run_player_server(player_factory, KIFGameState)
