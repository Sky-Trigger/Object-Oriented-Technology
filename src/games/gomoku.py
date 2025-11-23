# 五子棋游戏引擎，实现五子棋规则，包括落子和五连判断
from core.game_engine import GameEngine
from core.models import GameResult, Move, Position


class GomokuEngine(GameEngine):
    def play_move(self, position):
        # 执行落子，检查胜利条件
        if self.is_finished():
            raise ValueError("当前对局已结束")
        if not self.board.is_within_bounds(position):
            raise ValueError("落子超出棋盘范围")
        if self.board.get(position) is not None:
            raise ValueError("该位置已有棋子")
        current_color = self.current_player
        self._record_stone_placed(current_color)
        self.board.set(position, current_color)
        move = Move(position, current_color)
        self._push_move(move)
        if self._check_five_in_row(position):
            self._winner = GameResult(current_color, "连成五子")
        elif len(self.history) == self.board.size * self.board.size:
            self._winner = GameResult(None, "棋盘已满，平局")

    def _check_five_in_row(self, position):
        # 检查是否五连
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            line_length = self._count_in_direction(position, dr, dc)
            line_length += self._count_in_direction(position, -dr, -dc)
            line_length += 1
            if line_length >= 5:
                return True
        return False

    def _count_in_direction(self, position, dr, dc):
        # 计算方向上的连子数
        count = 0
        row, col = position.row + dr, position.col + dc
        base_color = self.board.get(position)
        while 0 <= row < self.board.size and 0 <= col < self.board.size:
            if self.board.get(Position(row, col)) != base_color:
                break
            count += 1
            row, col = row + dr, col + dc
        return count

    def _undo_internal(self):
        # 悔棋内部逻辑
        last_move = self.history.pop()
        if last_move.position is not None:
            self.board.set(last_move.position, None)
            self._record_stone_removed(last_move.color)
        self.current_player = last_move.color
        self._winner = None
