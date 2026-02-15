from ast import Global
import tkinter as tk
from pet_window import PetWindow
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    root = tk.Tk()
    # 立即隐藏窗口，避免闪烁
    root.withdraw()

    # 尝试导入pystray
    try:
        from tray_manager import create_tray_manager
        
        # 先隐藏窗口，避免边框闪烁
        root.withdraw()
        app = PetWindow(root)
        
        # 创建托盘管理器
        tray_manager = create_tray_manager(app, root)
        
        # 延迟启动托盘，让窗口完全初始化后再显示
        root.update_idletasks()
        root.deiconify()  # 显示窗口（避免边框闪烁）
        root.after(500, lambda: tray_manager.run_detached())
        
        # 显示启动提示
        root.after(1000, lambda: app.chat_window.show_response(
            "小星: 你好呀！我是你的桌面宠物小星~ (◕‿◕✿)\n\n我会一直陪着你的哦！",
            is_ai=True
        ))
        
        root.mainloop()
        
    except ImportError:
        # 没有pystray时正常运行窗口
        print("未安装pystray，将只显示窗口。可运行: pip install pystray")
        root.deiconify()  # 显示窗口
        app = PetWindow(root)
        
        # 显示启动提示
        root.after(1000, lambda: app.chat_window.show_response(
            "小星: 你好呀！我是你的桌面宠物小星~ (◕‿◕✿)\n\n我会一直陪着你的哦！",
            is_ai=True
        ))
        
        root.mainloop()