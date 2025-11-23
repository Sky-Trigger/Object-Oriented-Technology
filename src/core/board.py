# 棋盘管理类，负责棋盘状态的存储、访问和序列化
from core.models import PlayerColor


class Board:
    def __init__(self, size):
        # 初始化棋盘，设置大小并创建网格
        if size < 8 or size > 19:
            raise ValueError("棋盘大小必须介于 8 到 19 之间")
        self.size = size
        self._grid = [[None for _ in range(size)] for _ in range(size)]

    def reset(self):
        # 清空棋盘所有位置
        for row in self._grid:
            for col_index in range(self.size):
                row[col_index] = None

    def is_within_bounds(self, position):
        # 检查位置是否在棋盘范围内
        return 0 <= position.row < self.size and 0 <= position.col < self.size

    def get(self, position):
        # 获取指定位置的棋子颜色
        if not self.is_within_bounds(position):
            raise ValueError("该位置超出棋盘范围")
        return self._grid[position.row][position.col]

    def set(self, position, color):
        # 在指定位置放置棋子
        if not self.is_within_bounds(position):
            raise ValueError("该位置超出棋盘范围")
        self._grid[position.row][position.col] = color

    def serialize(self):
        # 将棋盘状态序列化为列表
        return [
            [None if cell is None else cell.value for cell in row] for row in self._grid
        ]

    def deserialize(self, payload):
        # 从序列化数据恢复棋盘状态
        if len(payload) != self.size:
            raise ValueError("棋盘数据尺寸不匹配")
        for row_index, row_payload in enumerate(payload):
            if len(row_payload) != self.size:
                raise ValueError("棋盘数据尺寸不匹配")
            for col_index, cell_value in enumerate(row_payload):
                self._grid[row_index][col_index] = (
                    None if cell_value is None else PlayerColor(cell_value)
                )
