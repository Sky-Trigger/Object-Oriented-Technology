# 数据模型和枚举定义，包括游戏类型、玩家颜色、位置、棋步和结果
from enum import Enum


class GameType(Enum):
    GOMOKU = "gomoku"
    GO = "go"


def game_type_from_string(value):
    # 从字符串转换为游戏类型
    normalized = value.strip().lower()
    for member in GameType:
        if member.value == normalized:
            return member
    raise ValueError(f"Unsupported game type: {value}")


class PlayerColor(Enum):
    BLACK = "B"
    WHITE = "W"

    def opponent(self):
        # 获取对手颜色
        if self is PlayerColor.BLACK:
            return PlayerColor.WHITE
        return PlayerColor.BLACK


class Position:
    def __init__(self, row, col):
        # 初始化位置
        self.row = row
        self.col = col

    def to_tuple(self):
        # 转换为元组
        return self.row, self.col

    def __iter__(self):
        # 迭代器
        yield self.row
        yield self.col

    def __eq__(self, other):
        # 判断相等
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self):
        # 计算哈希
        return hash((self.row, self.col))

    def __repr__(self):
        # 字符串表示
        return f"Position(row={self.row}, col={self.col})"


class Move:
    def __init__(self, position, color, captures=None):
        # 初始化移动
        self.position = position
        self.color = color
        self.captures = captures or []

    def is_pass(self):
        # 检查是否虚手
        return self.position is None

    def serialize(self):
        # 序列化移动
        if self.position is None:
            pos_payload = None
        else:
            pos_payload = {"row": self.position.row, "col": self.position.col}
        return {
            "position": pos_payload,
            "color": self.color.value,
            "captures": [{"row": pos.row, "col": pos.col} for pos in self.captures],
        }


def move_from_payload(payload):
    # 从载荷创建移动
    pos_payload = payload.get("position")
    if pos_payload is None:
        position = None
    else:
        position = Position(pos_payload["row"], pos_payload["col"])
    captures = []
    for capture in payload.get("captures", []):
        captures.append(Position(capture["row"], capture["col"]))
    color = PlayerColor(payload["color"])
    return Move(position, color, captures)


class GameResult:
    def __init__(self, winner, reason):
        # 初始化游戏结果
        self.winner = winner
        self.reason = reason

    def __repr__(self):
        # 字符串表示
        if self.winner is None:
            return f"GameResult(draw, reason={self.reason})"
        return f"GameResult(winner={self.winner.name}, reason={self.reason})"
