# 游戏引擎基类，定义游戏流程和通用逻辑，子类实现具体规则
from core.board import Board
from core.models import GameResult, Move, PlayerColor, Position, move_from_payload


class GameEngine:
    def __init__(self, board_size, max_undo=3):
        # 初始化引擎，设置棋盘和计数器
        self.board = Board(board_size)
        self.current_player = PlayerColor.BLACK
        self.history = []
        self.captured_by_color = {}
        self._winner = None
        self.max_undo = max_undo
        self._undo_used = {}
        self._stones_remaining = {}
        self._stones_on_board = {}
        self._reset_counters()

    def restart(self):
        # 重置游戏状态
        self.board.reset()
        self.history.clear()
        self._winner = None
        self.current_player = PlayerColor.BLACK
        self._reset_counters()

    def play_move(self, position):
        # 执行落子，子类实现
        raise NotImplementedError

    def pass_turn(self):
        # 执行虚手，默认不支持
        raise ValueError("当前游戏模式不支持虚手")

    def undo(self):
        # 执行悔棋
        if not self.history:
            raise ValueError("暂无可悔的棋步")
        last_move = self.history[-1]
        if self._undo_used[last_move.color] >= self.max_undo:
            raise ValueError("该玩家的悔棋次数已用尽")
        self._undo_used[last_move.color] += 1
        self._undo_internal()

    def _undo_internal(self):
        # 悔棋内部逻辑，子类实现
        raise NotImplementedError

    def resign(self, color):
        # 认输
        if self.is_finished():
            raise ValueError("当前对局已结束")
        winner = color.opponent()
        self._winner = GameResult(winner, "对手认输")

    def is_finished(self):
        # 检查游戏是否结束
        return self._winner is not None

    def get_result(self):
        # 获取游戏结果
        return self._winner

    def serialize(self):
        # 序列化游戏状态
        return {
            "board_size": self.board.size,
            "board": self.board.serialize(),
            "current_player": self.current_player.value,
            "history": [move.serialize() for move in self.history],
            "captured": {
                color.value: self.captured_by_color[color] for color in PlayerColor
            },
            "undo_used": {color.value: self._undo_used[color] for color in PlayerColor},
            "stones_remaining": {
                color.value: self._stones_remaining[color] for color in PlayerColor
            },
            "stones_on_board": {
                color.value: self._stones_on_board[color] for color in PlayerColor
            },
            "winner": (
                None
                if not self._winner
                else {
                    "winner": (
                        None
                        if self._winner.winner is None
                        else self._winner.winner.value
                    ),
                    "reason": self._winner.reason,
                }
            ),
        }

    def deserialize(self, payload):
        # 反序列化游戏状态
        if payload.get("board_size") != self.board.size:
            raise ValueError("载入数据的棋盘尺寸与当前设置不符")
        self.board.deserialize(payload["board"])
        self.current_player = PlayerColor(payload["current_player"])
        self.history = [move_from_payload(item) for item in payload.get("history", [])]
        for color in PlayerColor:
            self.captured_by_color[color] = payload.get("captured", {}).get(
                color.value, 0
            )
            self._undo_used[color] = payload.get("undo_used", {}).get(color.value, 0)
        if payload.get("stones_remaining") and payload.get("stones_on_board"):
            for color in PlayerColor:
                self._stones_remaining[color] = payload["stones_remaining"].get(
                    color.value, 0
                )
                self._stones_on_board[color] = payload["stones_on_board"].get(
                    color.value, 0
                )
        else:
            self._recalculate_stone_counters()
        winner_payload = payload.get("winner")
        if winner_payload:
            winner_value = winner_payload.get("winner")
            self._winner = GameResult(
                None if winner_value is None else PlayerColor(winner_value),
                winner_payload.get("reason", ""),
            )
        else:
            self._winner = None

    def _push_move(self, move):
        # 添加棋步并切换玩家
        self.history.append(move)
        self.current_player = self.current_player.opponent()

    def _record_stone_placed(self, color):
        # 记录落子
        remaining = self._stones_remaining[color]
        if remaining <= 0:
            raise ValueError("No stones remaining for player")
        self._stones_remaining[color] = remaining - 1
        self._stones_on_board[color] += 1

    def _record_stone_removed(self, color):
        # 记录提子
        if self._stones_on_board[color] > 0:
            self._stones_on_board[color] -= 1
        self._stones_remaining[color] += 1

    def stones_on_board(self, color):
        # 获取在盘棋子数
        return self._stones_on_board[color]

    def stones_remaining(self, color):
        # 获取剩余棋子数
        return self._stones_remaining[color]

    def undo_remaining(self, color):
        # 获取剩余悔棋次数
        return max(0, self.max_undo - self._undo_used[color])

    def _recalculate_stone_counters(self):
        # 重新计算棋子计数
        counts = {color: 0 for color in PlayerColor}
        for row in range(self.board.size):
            for col in range(self.board.size):
                occupant = self.board.get(Position(row, col))
                if occupant is not None:
                    counts[occupant] += 1
        total_slots = self.board.size * self.board.size
        for color, count in counts.items():
            self._stones_on_board[color] = count
            self._stones_remaining[color] = max(total_slots - count, 0)

    def _reset_counters(self):
        # 重置所有计数器
        total_slots = self.board.size * self.board.size
        for color in PlayerColor:
            self.captured_by_color[color] = 0
            self._undo_used[color] = 0
            self._stones_on_board[color] = 0
            self._stones_remaining[color] = total_slots
