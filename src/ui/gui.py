# 图形用户界面模块，使用Tkinter实现棋盘显示和交互
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from core.models import GameType, PlayerColor, Position, game_type_from_string


class GuiApp:
    def __init__(self, controller):
        # 初始化GUI应用
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("棋类对战平台")
        self.root.configure(bg="#f7f5f0")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.canvas_size = 600
        self._canvas_width = self.canvas_size
        self._canvas_height = self.canvas_size
        self._board_area = None
        self.game_type_options = {"五子棋": "gomoku", "围棋": "go"}
        self.game_type_var = tk.StringVar(value="五子棋")
        self.board_size_var = tk.StringVar(value="15")
        self.pass_button = None
        self._result_notified = False
        self.info_vars = {
            "game": tk.StringVar(value="游戏: --"),
            "turn": tk.StringVar(value="当前行棋方: --"),
            "black": tk.StringVar(value="黑方: 在盘 -- / 库存 -- / 悔棋 --"),
            "white": tk.StringVar(value="白方: 在盘 -- / 库存 -- / 悔棋 --"),
        }
        self._build_layout()
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self._update_pass_button_state()
        self._refresh_board()

    def _build_layout(self):
        # 构建界面布局
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="游戏类型: ").pack(side=tk.LEFT)
        game_selector = ttk.Combobox(
            control_frame,
            textvariable=self.game_type_var,
            values=list(self.game_type_options.keys()),
            state="readonly",
            width=10,
        )
        game_selector.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="棋盘大小: ").pack(side=tk.LEFT, padx=(10, 0))
        size_entry = ttk.Entry(control_frame, textvariable=self.board_size_var, width=5)
        size_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="开始对局", command=self._start_game).pack(
            side=tk.LEFT, padx=5
        )
        self.pass_button = ttk.Button(
            control_frame, text="虚手(围棋)", command=self._pass_turn
        )
        self.pass_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="悔棋", command=self._undo_move).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="认输", command=self._resign).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="保存局面", command=self._save_game).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="读取存档", command=self._load_game).pack(
            side=tk.LEFT, padx=5
        )

        info_frame = tk.Frame(main_frame, bg="#f7f5f0", pady=2)
        info_frame.pack(fill=tk.X, pady=(8, 4))
        info_colors = {
            "game": "#7a4b12",
            "turn": "#0f5c8e",
            "black": "#1d7b32",
            "white": "#8a1f4f",
        }
        self._info_labels = {}
        for key in ("game", "turn", "black", "white"):
            label = tk.Label(
                info_frame,
                textvariable=self.info_vars[key],
                fg=info_colors[key],
                bg="#f7f5f0",
                font=("Microsoft YaHei", 10),
                anchor="w",
            )
            label.pack(side=tk.LEFT, padx=10)
            self._info_labels[key] = label

        board_container = ttk.Frame(main_frame, padding=(0, 12, 0, 4))
        board_container.pack(fill=tk.BOTH, expand=True)
        board_container.columnconfigure(0, weight=1)
        board_container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            board_container,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#f5deb3",
            highlightthickness=2,
            highlightbackground="#c9a96c",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._handle_canvas_resize)

    def _read_board_size(self):
        # 读取棋盘大小
        try:
            size = int(self.board_size_var.get())
        except ValueError:
            raise ValueError("棋盘大小必须是整数")
        if size < 8 or size > 19:
            raise ValueError("棋盘大小需介于 8 到 19 之间")
        return size

    def _start_game(self):
        # 开始游戏
        try:
            selected = self.game_type_var.get()
            internal_type = self.game_type_options.get(selected, selected)
            game_type = game_type_from_string(internal_type)
            size = self._read_board_size()
            self.controller.start_game(game_type, size)
            self._result_notified = False
            self._refresh_board()
            self._update_pass_button_state()
        except Exception as error:
            self._handle_error(error)

    def _restart_game(self):
        # 重启游戏
        try:
            self.controller.restart()
            self._result_notified = False
            self._refresh_board()
            self._update_pass_button_state()
        except Exception as error:
            self._handle_error(error)

    def _pass_turn(self):
        # 执行虚手
        try:
            self.controller.pass_turn()
            self._refresh_board()
        except Exception as error:
            self._handle_error(error)

    def _undo_move(self):
        # 执行悔棋
        try:
            self.controller.undo()
            self._refresh_board()
        except Exception as error:
            self._handle_error(error)

    def _resign(self):
        # 认输
        try:
            self.controller.resign()
            self._refresh_board()
        except Exception as error:
            self._handle_error(error)

    def _save_game(self):
        # 保存游戏
        if self.controller.engine is None:
            messagebox.showinfo("提示", "请先开始对局，再执行保存。")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not file_path:
            return
        try:
            self.controller.save(file_path)
        except Exception as error:
            self._handle_error(error)

    def _load_game(self):
        # 加载游戏
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        try:
            self.controller.load(file_path)
            self._result_notified = False
            self._refresh_board()
            self._update_pass_button_state()
        except Exception as error:
            self._handle_error(error)

    def _on_canvas_click(self, event):
        # 处理画布点击
        if self.controller.engine is None:
            messagebox.showinfo("提示", "请先开始对局，再在棋盘落子。")
            return
        if not self._board_area:
            return
        start_x, start_y, end_x, end_y, cell = self._board_area
        if not (start_x <= event.x <= end_x and start_y <= event.y <= end_y):
            return
        size = self.controller.board_size
        relative_x = event.x - start_x
        relative_y = event.y - start_y
        col = int((relative_x + cell / 2) // cell)
        row = int((relative_y + cell / 2) // cell)
        if not (0 <= col < size and 0 <= row < size):
            return
        try:
            self.controller.place_stone(row, col)
            self._refresh_board()
        except Exception as error:
            self._handle_error(error)

    def _refresh_board(self):
        # 刷新棋盘显示
        self.canvas.delete("all")
        self._update_pass_button_state()
        width = self._canvas_width or self.canvas.winfo_width()
        height = self._canvas_height or self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        self.canvas.create_rectangle(0, 0, width, height, fill="#f5deb3", outline="")
        if self.controller.engine is None:
            self._board_area = None
            self._update_info_panel()
            self._result_notified = False
            return
        size = self.controller.board_size
        cell = min(width, height) / (size + 1)
        grid_span = cell * (size - 1)
        start_x = (width - grid_span) / 2
        start_y = (height - grid_span) / 2
        end_x = start_x + grid_span
        end_y = start_y + grid_span
        self._board_area = (start_x, start_y, end_x, end_y, cell)
        margin = cell * 0.5
        self.canvas.create_rectangle(
            start_x - margin,
            start_y - margin,
            end_x + margin,
            end_y + margin,
            fill="#fbe3b1",
            outline="",
        )
        for index in range(size):
            x = start_x + index * cell
            y = start_y + index * cell
            self.canvas.create_line(start_x, y, end_x, y, fill="#6d4c2f")
            self.canvas.create_line(x, start_y, x, end_y, fill="#6d4c2f")
        for point in self._star_points(size):
            cx = start_x + point[1] * cell
            cy = start_y + point[0] * cell
            radius = max(2, cell * 0.08)
            self.canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill="#4b3825",
                outline="",
            )
        for row in range(size):
            for col in range(size):
                stone = self.controller.engine.board.get(Position(row, col))
                if stone is None:
                    continue
                center_x = start_x + col * cell
                center_y = start_y + row * cell
                radius = cell * 0.4
                fill_color = "black" if stone == PlayerColor.BLACK else "white"
                outline_color = "white" if stone == PlayerColor.BLACK else "black"
                self.canvas.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=fill_color,
                    outline=outline_color,
                    width=2,
                )
        self._update_info_panel()
        self._notify_game_end()

    def _handle_canvas_resize(self, event):
        # 处理画布大小变化
        if event.width == self._canvas_width and event.height == self._canvas_height:
            return
        self._canvas_width = event.width
        self._canvas_height = event.height
        self._refresh_board()

    def _update_pass_button_state(self):
        # 更新虚手按钮状态
        if self.pass_button is None:
            return
        if self.controller.engine is None or self.controller.game_type != GameType.GO:
            self.pass_button.config(state=tk.DISABLED)
        else:
            self.pass_button.config(state=tk.NORMAL)

    def _handle_error(self, error):
        # 处理错误
        if isinstance(error, (ValueError, IOError)):
            messagebox.showerror("错误", str(error))
        else:
            messagebox.showerror("错误", f"出现未知异常: {error}")

    def run(self):
        # 运行应用
        self.root.mainloop()

    def _update_info_panel(self):
        # 更新信息面板
        if self.controller.engine is None:
            self.info_vars["game"].set("游戏: --")
            self.info_vars["turn"].set("当前行棋方: --")
            self.info_vars["black"].set("黑方: 在盘 -- / 库存 -- / 悔棋 --")
            self.info_vars["white"].set("白方: 在盘 -- / 库存 -- / 悔棋 --")
            return
        engine = self.controller.engine
        size = self.controller.board_size
        game_label = (
            "五子棋"
            if self.controller.game_type == GameType.GOMOKU
            else "围棋" if self.controller.game_type == GameType.GO else "未知游戏"
        )
        self.info_vars["game"].set(f"游戏: {game_label} {size}x{size}")
        current = "黑方" if engine.current_player == PlayerColor.BLACK else "白方"
        self.info_vars["turn"].set(f"当前行棋方: {current}")
        snapshot = self.controller.get_resource_snapshot()
        for color, label in [(PlayerColor.BLACK, "黑方"), (PlayerColor.WHITE, "白方")]:
            data = snapshot[color]
            self.info_vars["black" if color == PlayerColor.BLACK else "white"].set(
                f"{label}: 在盘{data['stones_on_board']}枚，库存{data['stones_remaining']}枚，悔棋余量{data['undo_remaining']}次"
            )

    def _star_points(self, size):
        # 获取星位点
        if size < 9:
            return []
        if size in (9, 13, 19):
            offsets = {9: [2, 4, 6], 13: [3, 6, 9], 19: [3, 9, 15]}[size]
        else:
            offsets = [2, size // 2, size - 3]
        return [(r, c) for r in offsets for c in offsets]

    def _notify_game_end(self):
        # 通知游戏结束
        engine = self.controller.engine
        if not engine or not engine.is_finished() or self._result_notified:
            return
        result = engine.get_result()
        if result.winner is None:
            message = f"结果: 平局\n{result.reason}"
        else:
            winner = "黑方" if result.winner == PlayerColor.BLACK else "白方"
            message = f"胜者: {winner}\n{result.reason}"
        messagebox.showinfo("对局结束", message)
        self._result_notified = True


def launch_gui(controller):
    # 启动GUI
    app = GuiApp(controller)
    app.run()
