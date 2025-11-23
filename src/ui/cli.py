# 命令行界面模块，实现基于命令的游戏交互
import sys

from core.controller import GameController
from core.models import GameType, game_type_from_string


class Command:
    def __init__(self, name, usage, description, handler):
        # 初始化命令
        self.name = name
        self.usage = usage
        self.description = description
        self.handler = handler


COMMAND_SPECS = (
    ("start", "start <gomoku|go> <size>", "Start a new game", "_cmd_start"),
    ("move", "move <row> <col>", "Place a stone", "_cmd_move"),
    ("pass", "pass", "Pass turn (Go only)", "_cmd_pass"),
    ("undo", "undo", "Undo last move", "_cmd_undo"),
    ("resign", "resign", "Resign current game", "_cmd_resign"),
    ("restart", "restart", "Restart current game", "_cmd_restart"),
    ("save", "save <file>", "Save current game", "_cmd_save"),
    ("load", "load <file>", "Load saved game", "_cmd_load"),
    ("board", "board", "Display board", "_cmd_board"),
    ("status", "status", "Show game status", "_cmd_status"),
    ("hint", "hint", "Toggle prompts", "_cmd_hint"),
    ("help", "help", "List commands", "_cmd_help"),
    ("gui", "gui", "Launch GUI", "_cmd_gui"),
    ("exit", "exit", "Exit program", "_cmd_exit"),
)


class ConsoleClient:
    def __init__(self):
        # 初始化控制台客户端
        self.controller = GameController()
        self.commands = {}
        self.running = True
        self.show_prompts = True
        self._register_commands()
        self.gui_launcher = None

    def _register_commands(self):
        # 注册命令
        for name, usage, description, handler in COMMAND_SPECS:
            self.commands[name] = Command(
                name, usage, description, getattr(self, handler)
            )

    def attach_gui_launcher(self, launcher):
        # 附加GUI启动器
        self.gui_launcher = launcher

    def run(self):
        # 运行命令循环
        print("Chess Platform CLI - type 'help' for instructions")
        while self.running:
            try:
                if self.show_prompts:
                    print(
                        "Available commands: start, move, pass, undo, resign, restart, save, load, board, status, hint, help, gui, exit"
                    )
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break
            if not raw:
                continue
            tokens = raw.split()
            command_name = tokens[0].lower()
            args = tokens[1:]
            command = self.commands.get(command_name)
            if not command:
                print("Unknown command. Type 'help' for a list of commands.")
                continue
            try:
                command.handler(args)
            except (ValueError, IOError) as error:
                print(f"错误: {error}")
            except Exception as unexpected:
                print(f"未知错误: {unexpected}")

    def _cmd_start(self, args):
        # 开始新游戏
        if len(args) != 2:
            raise ValueError("Usage: start <gomoku|go> <size>")
        try:
            game_type = game_type_from_string(args[0])
        except ValueError as error:
            raise ValueError(str(error))
        try:
            board_size = int(args[1])
        except ValueError:
            raise ValueError("Board size must be an integer")
        if board_size < 8 or board_size > 19:
            raise ValueError("Board size must be between 8 and 19")
        self.controller.start_game(game_type, board_size)
        print(f"Started {game_type.value} on a {board_size}x{board_size} board.")
        self._cmd_board([])

    def _cmd_move(self, args):
        # 执行落子
        if len(args) != 2:
            raise ValueError("Usage: move <row> <col>")
        row = self._parse_coordinate(args[0])
        col = self._parse_coordinate(args[1])
        self.controller.place_stone(row - 1, col - 1)
        self._cmd_board([])

    def _parse_coordinate(self, value):
        # 解析坐标
        try:
            coordinate = int(value)
        except ValueError:
            raise ValueError("Coordinates must be integers")
        if coordinate <= 0:
            raise ValueError("Coordinates must be positive")
        return coordinate

    def _cmd_pass(self, args):
        # 执行虚手
        self.controller.pass_turn()
        print("Turn passed.")

    def _cmd_undo(self, args):
        # 执行悔棋
        self.controller.undo()
        print("Reverted the last move.")

    def _cmd_resign(self, args):
        # 认输
        self.controller.resign()
        result = self.controller.engine.get_result()
        print(f"Game ended: {result.reason}")

    def _cmd_restart(self, args):
        # 重启游戏
        self.controller.restart()
        print("Game restarted.")
        self._cmd_board([])

    def _cmd_save(self, args):
        # 保存游戏
        if len(args) != 1:
            raise ValueError("Usage: save <file>")
        self.controller.save(args[0])
        print(f"Saved game to {args[0]}")

    def _cmd_load(self, args):
        # 加载游戏
        if len(args) != 1:
            raise ValueError("Usage: load <file>")
        self.controller.load(args[0])
        print(f"Loaded game from {args[0]}")
        self._cmd_board([])

    def _cmd_board(self, args):
        # 显示棋盘
        print(self.controller.get_board_display())

    def _cmd_status(self, args):
        # 显示状态
        print(self.controller.get_status())

    def _cmd_hint(self, args):
        # 切换提示
        self.show_prompts = not self.show_prompts
        print(f"Prompts {'enabled' if self.show_prompts else 'hidden'}.")

    def _cmd_help(self, args):
        # 显示帮助
        print("Available commands:")
        for cmd in self.commands.values():
            print(f"- {cmd.usage:<25} {cmd.description}")

    def _cmd_gui(self, args):
        # 启动GUI
        if self.gui_launcher:
            self.gui_launcher(self.controller)
        else:
            print("GUI launcher not configured.")

    def _cmd_exit(self, args):
        # 退出程序
        self.running = False
        print("Goodbye!")
        sys.exit(0)


def run_cli(gui_launcher=None):
    # 运行CLI
    client = ConsoleClient()
    if gui_launcher is not None:
        client.attach_gui_launcher(gui_launcher)
    client.run()
