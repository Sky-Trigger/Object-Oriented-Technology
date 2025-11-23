# 围棋游戏引擎，实现围棋规则，包括提子、禁入点判断和胜负计算
from core.game_engine import GameEngine
from core.models import GameResult, Move, PlayerColor, Position


class GoEngine(GameEngine):
    def __init__(self, board_size, max_undo=3):
        # 初始化围棋引擎
        super().__init__(board_size, max_undo)
        self.consecutive_passes = 0

    def play_move(self, position):
        # 执行落子，处理提子
        if self.is_finished():
            raise ValueError("当前对局已结束")
        if not self.board.is_within_bounds(position):
            raise ValueError("落子超出棋盘范围")
        if self.board.get(position) is not None:
            raise ValueError("该位置已有棋子")
        self._record_stone_placed(self.current_player)
        self.board.set(position, self.current_player)
        captured_positions = self._capture_adjacent_groups(position)
        if not self._has_liberty(position):
            if captured_positions:
                pass
            else:
                self.board.set(position, None)
                self._record_stone_removed(self.current_player)
                raise ValueError("禁入点: 落子后本方无气")
        move = Move(position, self.current_player, captured_positions)
        self.captured_by_color[self.current_player] += len(captured_positions)
        self.consecutive_passes = 0
        self._push_move(move)

    def pass_turn(self):
        # 执行虚手
        if self.is_finished():
            raise ValueError("当前对局已结束")
        move = Move(None, self.current_player)
        self.consecutive_passes += 1
        self._push_move(move)
        if self.consecutive_passes >= 2:
            self._winner = self._score_game()

    def _capture_adjacent_groups(self, position):
        # 提子相邻敌方棋子
        opponent = self.current_player.opponent()
        captured = []
        visited_keys = set()
        for neighbor in self._neighbors(position):
            if self.board.get(neighbor) != opponent:
                continue
            group = self._collect_group(neighbor)
            if self._group_has_liberty(group):
                continue
            for stone in group:
                key = stone.to_tuple()
                if key in visited_keys:
                    continue
                visited_keys.add(key)
                captured.append(stone)
        for stone in captured:
            self.board.set(stone, None)
            self._record_stone_removed(opponent)
        return captured

    def _neighbors(self, position):
        # 获取邻居位置
        neighbors = []
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = position.row + dr, position.col + dc
            if 0 <= nr < self.board.size and 0 <= nc < self.board.size:
                neighbors.append(Position(nr, nc))
        return neighbors

    def _collect_group(self, start):
        # 收集连通棋子组
        target_color = self.board.get(start)
        if target_color is None:
            return []
        stack = [start]
        visited = set()
        group = []
        while stack:
            current = stack.pop()
            key = current.to_tuple()
            if key in visited:
                continue
            visited.add(key)
            if self.board.get(current) != target_color:
                continue
            group.append(current)
            stack.extend(self._neighbors(current))
        return group

    def _group_has_liberty(self, group):
        # 检查棋子组是否有气
        for stone in group:
            for neighbor in self._neighbors(stone):
                if self.board.get(neighbor) is None:
                    return True
        return False

    def _has_liberty(self, position):
        # 检查位置是否有气
        group = self._collect_group(position)
        return self._group_has_liberty(group)

    def _score_game(self):
        # 计算游戏得分
        territory = self._compute_territory()
        black_score = territory[PlayerColor.BLACK]
        white_score = territory[PlayerColor.WHITE]
        black_score += self.captured_by_color[PlayerColor.BLACK]
        white_score += self.captured_by_color[PlayerColor.WHITE]
        black_score += self._count_stones(PlayerColor.BLACK)
        white_score += self._count_stones(PlayerColor.WHITE)
        if black_score > white_score:
            return GameResult(
                PlayerColor.BLACK, f"黑方以 {black_score}:{white_score} 获胜"
            )
        if white_score > black_score:
            return GameResult(
                PlayerColor.WHITE, f"白方以 {white_score}:{black_score} 获胜"
            )
        return GameResult(None, "双方比分相同，平局")

    def _count_stones(self, color):
        # 计数棋子数
        return self.stones_on_board(color)

    def _compute_territory(self):
        # 计算领土
        visited = set()
        territory = {PlayerColor.BLACK: 0, PlayerColor.WHITE: 0}
        for row in range(self.board.size):
            for col in range(self.board.size):
                pos = Position(row, col)
                if self.board.get(pos) is None and pos.to_tuple() not in visited:
                    region, owners = self._explore_empty_region(pos, visited)
                    if len(owners) == 1:
                        territory[owners.pop()] += len(region)
        return territory

    def _explore_empty_region(self, start, visited):
        # 探索空区域
        stack = [start]
        region = []
        owners = set()
        while stack:
            current = stack.pop()
            key = current.to_tuple()
            if key in visited:
                continue
            visited.add(key)
            if self.board.get(current) is not None:
                continue
            region.append(current)
            for neighbor in self._neighbors(current):
                occupant = self.board.get(neighbor)
                if occupant is None:
                    stack.append(neighbor)
                else:
                    owners.add(occupant)
        return region, owners

    def _undo_internal(self):
        # 悔棋内部逻辑
        last_move = self.history.pop()
        self.current_player = last_move.color
        if last_move.position is None:
            if self.consecutive_passes > 0:
                self.consecutive_passes -= 1
            self._winner = None
            return
        self.board.set(last_move.position, None)
        self._record_stone_removed(last_move.color)
        opponent = last_move.color.opponent()
        for stone in last_move.captures:
            self.board.set(stone, opponent)
            self._record_stone_placed(opponent)
        self.captured_by_color[last_move.color] -= len(last_move.captures)
        self.consecutive_passes = 0
        self._winner = None
