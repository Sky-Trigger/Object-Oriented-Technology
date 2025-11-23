# 游戏控制器，负责协调游戏引擎和用户界面，提供统一的游戏操作接口
from core.models import GameResult, GameType, PlayerColor, Position
from core import persistence
from games.gomoku import GomokuEngine
from games.go import GoEngine


def create_engine(game_type, board_size):
    # 根据游戏类型创建对应的引擎实例
    if game_type == GameType.GOMOKU:
        return GomokuEngine(board_size)
    if game_type == GameType.GO:
        return GoEngine(board_size)
    raise ValueError("Unsupported game type")


class GameController:
    def __init__(self):
        # 初始化控制器，无当前游戏
        self.engine = None
        self.game_type = None
        self.board_size = 0

    def start_game(self, game_type, board_size):
        # 开始新游戏，创建引擎
        self.engine = create_engine(game_type, board_size)
        self.game_type = game_type
        self.board_size = board_size

    def _require_engine(self):
        # 确保有活跃游戏，否则抛异常
        if self.engine is None:
            raise ValueError("当前没有运行中的对局，请先执行开始命令。")
        return self.engine

    def place_stone(self, row, col):
        # 在指定位置落子
        engine = self._require_engine()
        position = Position(row, col)
        engine.play_move(position)

    def pass_turn(self):
        # 执行虚手，仅围棋支持
        engine = self._require_engine()
        if self.game_type != GameType.GO:
            raise ValueError("只有围棋对局才能执行虚手操作")
        engine.pass_turn()

    def undo(self):
        # 悔棋
        engine = self._require_engine()
        engine.undo()

    def resign(self, color=None):
        # 认输，默认当前玩家
        engine = self._require_engine()
        active_color = color or engine.current_player
        engine.resign(active_color)

    def restart(self):
        # 重新开始当前游戏
        engine = self._require_engine()
        engine.restart()

    def save(self, file_path):
        # 保存游戏状态到文件
        engine = self._require_engine()
        payload = {
            "game_type": None if self.game_type is None else self.game_type.value,
            "state": engine.serialize(),
        }
        persistence.save_game(file_path, payload)

    def load(self, file_path):
        # 从文件加载游戏状态
        payload = persistence.load_game(file_path)
        if "game_type" not in payload or "state" not in payload:
            raise IOError("存档文件格式不正确")
        game_type_value = payload["game_type"]
        state = payload["state"]
        try:
            game_type = GameType(game_type_value)
        except ValueError as error:
            raise IOError(f"存档中包含未知的游戏类型: {error}")
        board_size = state.get("board_size")
        if board_size is None:
            raise IOError("存档文件缺少棋盘大小信息")
        self.engine = create_engine(game_type, board_size)
        self.engine.deserialize(state)
        self.game_type = game_type
        self.board_size = board_size

    def get_board_display(self):
        # 获取棋盘文本显示
        engine = self._require_engine()
        header = "    " + " ".join(f"{i:2d}" for i in range(1, engine.board.size + 1))
        rows = [header]
        for row in range(engine.board.size):
            tokens = []
            for col in range(engine.board.size):
                cell = engine.board.get(Position(row, col))
                tokens.append(
                    "." if cell is None else "X" if cell == PlayerColor.BLACK else "O"
                )
            rows.append(f"{row + 1:2d} | " + "  ".join(tokens))
        return "\n".join(rows)

    def get_status(self):
        # 获取游戏状态信息
        engine = self._require_engine()
        snapshot = self.get_resource_snapshot()
        status_parts = [
            f"游戏: {self._game_type_label()} {self.board_size}x{self.board_size}",
            f"当前行棋方: {self._color_label(engine.current_player)}",
            self._format_resource_line(PlayerColor.BLACK, snapshot),
            self._format_resource_line(PlayerColor.WHITE, snapshot),
        ]
        if engine.is_finished():
            result = engine.get_result()
            status_parts.append(
                "结果: 平局"
                if result.winner is None
                else f"胜者: {self._color_label(result.winner)}"
            )
            status_parts.append(f"结束原因: {result.reason}")
        return " | ".join(status_parts)

    def get_resource_snapshot(self):
        # 获取资源快照（棋子数量等）
        engine = self._require_engine()
        snapshot = {}
        for color in (PlayerColor.BLACK, PlayerColor.WHITE):
            snapshot[color] = {
                "stones_on_board": engine.stones_on_board(color),
                "stones_remaining": engine.stones_remaining(color),
                "undo_remaining": engine.undo_remaining(color),
            }
        return snapshot

    def _game_type_label(self):
        # 获取游戏类型标签
        if self.game_type == GameType.GOMOKU:
            return "五子棋"
        if self.game_type == GameType.GO:
            return "围棋"
        return "未知游戏"

    def _color_label(self, color):
        # 获取玩家颜色标签
        return "黑方" if color == PlayerColor.BLACK else "白方"

    def _format_resource_line(self, color, snapshot):
        # 格式化资源信息行
        data = snapshot[color]
        label = self._color_label(color)
        return (
            f"{label}: 在盘{data['stones_on_board']}枚，"
            f"库存{data['stones_remaining']}枚，"
            f"悔棋余量{data['undo_remaining']}次"
        )
