#!/usr/bin/python3

import argparse
import faulthandler
import inspect
import logging

from pygdl.players import (
    AlphaBeta,
    BoundedDepth,
    CompulsiveDeliberation,
    Legal,
    Minimax,
    MonteCarlo,
    MonteCarloTreeSearch,
    PlayerFactory,
    Random,
    SequentialPlanner,
)
player_classes = [
    AlphaBeta,
    BoundedDepth,
    CompulsiveDeliberation,
    Legal,
    Minimax,
    MonteCarlo,
    MonteCarloTreeSearch,
    Random,
    SequentialPlanner,
]


class LogLevel(object):
    levels = ['debug', 'info', 'warning', 'error', 'critical']

    def __init__(self, level_string):
        if level_string in self.levels:
            self.level = getattr(logging, level_string.upper())
        else:
            self.level = int(level_string)


def main():
    # faulthandler.enable()  # XXX
    parser = argparse.ArgumentParser(description="General Game Player Server")
    parser.add_argument('-P', '--port', type=int, default=9147,
                        help="Port on which the server listens. (default 9147)")
    parser.add_argument('--log', type=LogLevel, default='info',
                        dest='log_level',
                        help=("Set logging level. "
                              "Either an integer value or one of: "
                              "{} (default '{}')".format(
                                  ', '.join(LogLevel.levels), 'info')))
    subparsers = parser.add_subparsers(
        title='Players', dest='player', metavar='PLAYER',
        help='Game player class.')
    subparsers.required = True

    for player in player_classes:
        player_doc = inspect.getdoc(player)
        player_help = (player_doc.splitlines()[0] if player_doc is not None
                       else None)
        player_parser = subparsers.add_parser(player.__name__, help=player_help)
        for param_name, description in player.PARAMETER_DESCRIPTIONS.items():
            if 'default' in description.dict:
                param_name = '--' + param_name
            player_parser.add_argument(param_name, **description.dict)

    args = parser.parse_args()

    from pygdl.gamestate import GeneralGameManager
    from pygdl.playerserver import run_player_server

    player_class_dict = {class_.__name__: class_
                         for class_ in player_classes}

    logging.basicConfig(level=args.log_level.level)
    player_class = player_class_dict[args.player]
    player_kwargs = {param_name: getattr(args, param_name)
                     for param_name
                     in player_class.PARAMETER_DESCRIPTIONS.keys()}
    player_factory = PlayerFactory(player_class, **player_kwargs)
    game_manager = GeneralGameManager()
    run_player_server(game_manager=game_manager,
                      player_factory=player_factory,
                      port=args.port,
                      search_for_open_port=True)

if __name__ == '__main__':
    main()
