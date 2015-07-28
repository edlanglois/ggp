import datetime
import http.server
import logging

from pygdl.sexpr import parse_s_expressions, to_s_expression_string

logger = logging.getLogger(__name__)


class MessageError(Exception):
    def __init__(self, reason):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return str(self.reason)


class ForbiddenMessageError(MessageError):
    pass


class BadMessageError(MessageError):
    pass


class ArgumentError(BadMessageError):
    pass


class NumberOfArgumentsError(ArgumentError):
    def __init__(self, message_type, arguments, expected_len):
        self.message_type = message_type
        self.arguments = arguments
        self.expected_len = expected_len

    def __str__(self):
        return ('Wrong number of arguments for message type "{!s}" '
                'expected {!s} arguments but got {!s}').format(
            self.message_type, self.expected_len, self.arguments)


# TODO: No need for game_state
class SerialGeneralGamePlayingMessageHandler(object):
    """Handles General-Game-Playing messages all in one thread."""
    class GameStuff(object):
        def __init__(self, game_state, player):
            self.game_state = game_state
            self.player = player

    class UnknownGameIDError(Exception):
        def __init__(self, id):
            self.id = id

    def __init__(self, player_factory, game_state_factory,
                 max_simultaneous_games=1):
        super().__init__()
        self.player_factory = player_factory
        self.game_state_factory = game_state_factory
        self.max_simultaneous_games = max_simultaneous_games
        self.games = dict()

    def handle_message(self, message):
        message_s_expressions = parse_s_expressions(message)
        message_s_expression = next(message_s_expressions)
        try:
            next(message_s_expressions)
            raise BadMessageError(
                "Message must contain exactly one S-Expression")
        except StopIteration:
            pass

        message_type = message_s_expression[0]
        try:
            handler = getattr(self, 'do_' + message_type)
        except AttributeError:
            logger.error("No handler for messsage type: " + message_type)
            return

        try:
            return handler(message_s_expression[1:])
        except self.UnknownGameIDError as e:
            logger.warning("Received message for unknown game id '%s'", e.id)

    def get_game(self, game_id):
        """Return the GameStuff associated with id"""
        try:
            return self.games[game_id]
        except KeyError as e:
            raise self.UnknownGameIDError(game_id) from e

    def make_info_response(self, is_available):
        return (('name', self.player_factory.player_name),
                ('status', 'available' if is_available else 'busy'))

    def do_info(self, args):
        logger.info("Received info message.")
        if args:
            raise NumberOfArgumentsError('info', args, 0)
        return self.make_info_response(
            len(self.games) < self.max_simultaneous_games)

    def do_start(self, args):
        logger.info("Received start message.")
        logger.debug("Num active games: " + str(len(self.games)))
        if len(args) != 5:
            raise NumberOfArgumentsError('start', args, 5)

        if len(self.games) >= self.max_simultaneous_games:
            raise ForbiddenMessageError(
                'Max simultaneous games ({!s}) reached'.format(
                    self.max_simultaneous_games))

        game_id = args[0]
        player_role = args[1]
        game_description = args[2]
        start_clock = datetime.timedelta(seconds=int(args[3]))
        play_clock = datetime.timedelta(seconds=int(args[4]))

        logger.debug("Game ID: " + game_id)
        logger.debug("Player Role: " + player_role)
        logger.debug("Start clock: " + str(start_clock))
        logger.debug("Play clock: " + str(play_clock))

        game_state = self.game_state_factory()
        game_state.load_game_from_s_expressions(game_description)

        player = self.player_factory(game_state, player_role,
                                     start_clock, play_clock)

        self.games[game_id] = self.GameStuff(game_state=game_state,
                                             player=player)
        return 'ready'

    def do_play(self, args):
        logger.info("Received play message.")
        if len(args) != 2:
            raise NumberOfArgumentsError('play', args, 2)

        game_id = args[0]
        new_moves = args[1]
        logger.debug("Game ID: " + game_id)
        logger.debug("New moves: " + str(new_moves))

        player = self.get_game(game_id).player

        if new_moves != 'nil':
            player.update_moves(new_moves)

        move = player.get_move()
        logger.debug("Chosen move: " + move)
        return move

    def do_stop(self, args):
        logger.info("Received stop message.")
        if len(args) != 2:
            raise NumberOfArgumentsError('stop', args, 2)

        game_id = args[0]
        new_moves = args[1]
        logger.debug("Game ID: " + game_id)
        logger.debug("New moves: " + str(new_moves))

        player = self.get_game(game_id).player

        if new_moves != 'nil':
            player.update_moves(new_moves)

        player.stop()
        return 'done'


    def do_abort(self, args):
        logger.info("Received abort message.")
        if len(args) != 1:
            raise NumberOfArgumentsError('abort', args, 1)

        game_id = args[0]
        logger.debug("Game ID: " + game_id)

        player = self.get_game(game_id).player
        player.abort()

        return 'done'


def make_general_game_playing_request_handler(message_handler):
    class GeneralGamePlayingRequestHandler(http.server.BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            super().__init__(request, client_address, server)

        def log_message(self, format_, *args):
            logger.debug("Sent: " + format_, *args)

        def do_POST(self):
            content_length = int(self.headers['content-length'])
            message_bytes = self.rfile.read(content_length)
            message = message_bytes.decode()
            message_lines = message.splitlines()

            response = None
            try:
                response = message_handler.handle_message(message_lines)
                response_code = 200
            except BadMessageError as e:
                logger.warn("Error processing message. Reason: " + str(e))
                response_code = 400
            except ForbiddenMessageError as e:
                logger.info("Refusing to process message. Reason: " + str(e))
                response_code = 403

            if response is None:
                response_str = ''
            else:
                response_str = to_s_expression_string(response)
            response_bytes = response_str.encode()

            self.send_response(response_code)
            self.send_header("Content-type", "text/acl")
            self.send_header("Content-length", len(response_bytes))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods",
                             "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Age", "86400")
            self.end_headers()
            self.wfile.write(response_bytes)

    return GeneralGamePlayingRequestHandler


def run_player_server(player_factory, game_state_factory, port=9147):
    handler = make_general_game_playing_request_handler(
        SerialGeneralGamePlayingMessageHandler(player_factory,
                                               game_state_factory))
    server = http.server.HTTPServer(('', port), handler)
    logger.info('Server listening on port {!s}'.format(port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Interrupt received. Stopping server.')
        pass
