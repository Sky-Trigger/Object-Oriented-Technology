# 程序入口，启动命令行界面并提供GUI启动功能
from ui import cli, gui


def main():
    # 启动命令行界面，传入GUI启动函数
    cli.run_cli(gui.launch_gui)


if __name__ == "__main__":
    main()
