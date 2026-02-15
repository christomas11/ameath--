import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, font
from PIL import Image, ImageTk,ImageGrab
import itertools
import random
import os
import json
import ctypes
import sys
import threading
import time
import base64
import io

# Windows API 常量
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

# 配置常量
TRANSPARENT_COLOR = "pink"
GIF_DIR = "gifs"
CONFIG_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "ameath_config.json"
)

# 缩放和透明度选项
SCALE_OPTIONS = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9]
TRANSPARENCY_OPTIONS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

# 运动配置
SPEED_X = 3
SPEED_Y = 2
STOP_CHANCE = 0.003
STOP_DURATION_MIN = 4000
STOP_DURATION_MAX = 8000
MOVE_INTERVAL = 30
JITTER_INTERVAL = 5
EDGE_ESCAPE_CHANCE = 0.3
RESPAWN_MARGIN = 50
TARGET_CHANGE_MIN = 200
TARGET_CHANGE_MAX = 500
OUTSIDE_TARGET_CHANCE = 0.4
FOLLOW_DISTANCE = 80
INERTIA_FACTOR = 0.95
INTENT_FACTOR = 0.05
JITTER = 0.15

# 状态机配置
MOTION_WANDER = "wander"
MOTION_FOLLOW = "follow"
MOTION_CURIOUS = "curious"
MOTION_REST = "rest"

# 状态参数
REST_CHANCE = 0.6
REST_DURATION_MIN = 1000
REST_DURATION_MAX = 3000
REST_DISTANCE = 20
FOLLOW_START_DIST = 200
FOLLOW_STOP_DIST = 60
SPEED_WANDER = 0.8
SPEED_FOLLOW = 1.2
SPEED_CURIOUS = 0.5
STAY_PUT_CHANCE = 0.3


def resource_path(relative_path):
    """获取资源路径（开发环境）"""
    return os.path.join(os.path.abspath("."), relative_path)


def load_config():
    """加载配置"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "scale_index": 3,
            "transparency_index": 0,
            "auto_startup": False,
            "click_through": True,
            "follow_mouse": False,
            "ai_enabled": False,
            "api_key": "",
        }


def save_config(config):
    """保存配置"""
    config_dir = os.path.dirname(CONFIG_FILE)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def flip_frames(pil_frames):
    """水平翻转所有PIL Image帧，返回PhotoImage"""
    flipped = []
    for img in pil_frames:
        flipped_img = ImageTk.PhotoImage(img.transpose(Image.Transpose.FLIP_LEFT_RIGHT))
        flipped.append(flipped_img)
    return flipped


def load_gif_frames(gif_path, scale=1.0):
    """加载并缩放GIF，返回(photoimage_frames, delays, pil_frames)"""
    photoimage_frames = []
    pil_frames = []
    delays = []
    gif = Image.open(gif_path)
    frame = None
    for i in itertools.count():
        try:
            gif.seek(i)
            frame = gif.convert("RGBA")
            w, h = frame.size
            new_w, new_h = int(w * scale), int(h * scale)
            # 确保缩放后尺寸有效
            if new_w <= 0 or new_h <= 0:
                new_w = max(1, new_w)
                new_h = max(1, new_h)
            resized = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
            photoimage_frames.append(ImageTk.PhotoImage(resized))
            pil_frames.append(resized)
            delays.append(gif.info.get("duration", 80))
        except EOFError:
            break
    # 确保至少有一帧
    if not photoimage_frames and frame is not None:
        photoimage_frames.append(
            ImageTk.PhotoImage(frame.resize((100, 100), Image.Resampling.LANCZOS))
        )
        pil_frames.append(frame.resize((100, 100), Image.Resampling.LANCZOS))
        delays.append(80)
    return photoimage_frames, delays, pil_frames

class ChatWindow:
    """聊天窗口类"""
    def __init__(self, parent, pet_window):
        self.parent = parent
        self.pet_window = pet_window

        # 聊天窗口基础配置
        self.base_width = 280
        self.base_height = 180
        self.max_width = 400
        self.max_height = 400
        self.min_width = 250
        self.min_height = 120
        
        # 当前窗口大小
        self.window_width = self.base_width
        self.window_height = self.base_height
        
        # 创建聊天窗口
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes("-topmost", True)
        self.window.configure(bg='#FFB6C1')  # 浅粉色背景
        
        # 创建主容器，带粉色边框
        self.main_frame = tk.Frame(self.window, bg='#FFB6C1', bd=3, relief=tk.RAISED)
        self.main_frame.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)
        
        # 内容区域（白色背景）
        self.content_frame = tk.Frame(self.main_frame, bg='white', bd=0)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 响应文本框 - 放在顶部
        self.response_frame = tk.Frame(self.content_frame, bg='white')
        self.response_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        
        # 创建文本框和滚动条
        self.response_text = tk.Text(
            self.response_frame,
            font=("Microsoft YaHei", 10),
            wrap=tk.WORD,
            height=4,
            bg='#FFF5F7',  # 浅粉色背景
            fg='#333333',
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=1,
            highlightcolor='#FFB6C1',
            highlightbackground='#FFB6C1',
            state=tk.DISABLED,
            cursor='arrow'
        )
        self.response_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 自定义滚动条样式
        scrollbar_style = ttk.Style()
        scrollbar_style.theme_use('clam')
        scrollbar_style.configure(
            "Custom.Vertical.TScrollbar",
            background='#FFB6C1',
            troughcolor='white',
            bordercolor='#FFB6C1',
            arrowcolor='white',
            relief=tk.FLAT
        )
        
        scrollbar = ttk.Scrollbar(
            self.response_frame,
            orient="vertical",
            command=self.response_text.yview,
            style="Custom.Vertical.TScrollbar"
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_text.config(yscrollcommand=scrollbar.set)
        
        # 输入框和发送按钮区域
        self.input_frame = tk.Frame(self.content_frame, bg='white')
        self.input_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # 输入框
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            self.input_frame,
            textvariable=self.input_var,
            font=("Microsoft YaHei", 10),
            width=25,
            relief=tk.FLAT,
            bg='#FFF5F7',
            fg='#333333',
            insertbackground='#FF69B4',  # 粉色光标
            borderwidth=2,
            highlightthickness=1,
            highlightcolor='#FFB6C1',
            highlightbackground='#FFB6C1'
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 绑定回车键
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        # 绑定Esc键关闭聊天窗口
        self.input_entry.bind('<Escape>', lambda e: self.hide())
        
        # 圆形发送按钮
        self.send_button_canvas = tk.Canvas(
            self.input_frame,
            width=32,
            height=32,
            bg='white',
            highlightthickness=0,
            relief=tk.FLAT
        )
        self.send_button_canvas.pack(side=tk.RIGHT)
        
        # 绘制圆形按钮
        self.button_bg = self.send_button_canvas.create_oval(
            2, 2, 30, 30,
            fill='#FF69B4',  # 粉色背景
            outline='#FF1493',  # 深粉色边框
            width=2
        )
        
        # 绘制向上的箭头
        self.button_arrow = self.send_button_canvas.create_text(
            16, 16,
            text="↑",
            font=("Microsoft YaHei", 14, "bold"),
            fill='white'
        )
        
        # 绑定点击事件
        self.send_button_canvas.bind("<Button-1>", lambda e: self.send_message())
        self.send_button_canvas.bind("<Enter>", self.on_button_hover)
        self.send_button_canvas.bind("<Leave>", self.on_button_leave)
        
        # 设置初始位置
        self.update_position()
        
        # 隐藏聊天窗口（默认不显示）
        self.window.withdraw()
        self.visible = False
        
        # 响应消息队列
        self.response_queue = []
        self.is_showing_response = False
        
    def on_button_hover(self, event):
        """鼠标悬停在按钮上时的效果"""
        self.send_button_canvas.itemconfig(self.button_bg, fill='#FF1493')
        self.send_button_canvas.config(cursor='hand2')
        
    def on_button_leave(self, event):
        """鼠标离开按钮时的效果"""
        self.send_button_canvas.itemconfig(self.button_bg, fill='#FF69B4')
        self.send_button_canvas.config(cursor='')
        
    def calculate_window_size(self, text):
        """根据文本内容计算窗口大小"""
        # 基础配置
        char_width = 8  # 平均每个字符的宽度
        line_height = 20  # 每行的高度
        
        # 计算文本需要的宽度和高度
        lines = text.split('\n')
        max_line_length = 0
        
        for line in lines:
            # 考虑中英文混合的字符长度
            line_length = len(line)
            max_line_length = max(max_line_length, line_length)
        
        # 计算需要的宽度
        required_width = min(
            max(self.min_width, max_line_length * char_width + 40), 
            self.max_width
        )
        
        # 计算需要的高度（考虑滚动条）
        required_lines = len(lines)
        if required_lines > 10:  # 最多显示10行，其余用滚动条
            required_lines = 10
            
        required_height = min(
            max(self.min_height, required_lines * line_height + 100),
            self.max_height
        )
        
        return int(required_width), int(required_height)
    
    def adjust_window_size(self):
        """根据响应内容调整窗口大小"""
        if not self.visible:
            return
            
        try:
            # 获取当前文本内容
            current_text = self.response_text.get(1.0, tk.END).strip()
            if not current_text:
                return
                
            # 计算新的大小
            new_width, new_height = self.calculate_window_size(current_text)
            
            # 更新窗口大小
            if new_width != self.window_width or new_height != self.window_height:
                self.window_width = new_width
                self.window_height = new_height
                self.update_position(adjust_only=True)
                
        except Exception as e:
            print(f"调整窗口大小出错: {e}")
    
    def update_position(self, adjust_only=False):
        """更新聊天窗口位置，跟随宠物"""
        if not adjust_only:
            # 计算基础位置 —— 使用宠物窗口的中心点判断左右侧
            pet_center_x = self.pet_window.x + self.pet_window.w // 2
            screen_mid = self.pet_window.screen_w / 2

            if pet_center_x < screen_mid:
                # 宠物中心在屏幕左侧 → 聊天窗口放在宠物右侧
                chat_x = self.pet_window.x + self.pet_window.w + 10
            else:
                # 宠物中心在屏幕右侧 → 聊天窗口放在宠物左侧
                chat_x = self.pet_window.x - self.window_width - 10

            # 垂直方向：与宠物窗口垂直居中
            chat_y = self.pet_window.y + (self.pet_window.h - self.window_height) // 2

        else:
            # 仅调整大小，保持当前窗口位置不变
            current_geometry = self.window.geometry()
            try:
                # 解析 geometry 字符串，格式如 "280x180+100+200"
                parts = current_geometry.replace('x', '+').split('+')
                if len(parts) >= 4:
                    # 最后两部分为 x, y 坐标
                    chat_x, chat_y = int(parts[-2]), int(parts[-1])
                else:
                    raise ValueError
            except:
                # 解析失败时回退到宠物右侧位置
                chat_x = self.pet_window.x + self.pet_window.w + 10
                chat_y = self.pet_window.y + (self.pet_window.h - self.window_height) // 2

        # 确保聊天窗口完全显示在屏幕内（保留 10 像素边距）
        screen_w = self.pet_window.screen_w
        screen_h = self.pet_window.screen_h

        if chat_x < 10:
            chat_x = 10
        elif chat_x + self.window_width > screen_w - 10:
            chat_x = screen_w - self.window_width - 10

        if chat_y < 10:
            chat_y = 10
        elif chat_y + self.window_height > screen_h - 10:
            chat_y = screen_h - self.window_height - 10

        self.window.geometry(f"{self.window_width}x{self.window_height}+{int(chat_x)}+{int(chat_y)}")
    
    def show(self):
        """显示聊天窗口"""
        if not self.visible:
            # 重置窗口大小到基础大小
            self.window_width = self.base_width
            self.window_height = self.base_height
            
            self.update_position()
            self.window.deiconify()
            self.visible = True
            self.input_entry.focus_set()
            
            # 清空之前的响应
            self.clear_response()
    
    def hide(self):
        """隐藏聊天窗口"""
        if self.visible:
            self.window.withdraw()
            self.visible = False
    
    def toggle(self):
        """切换聊天窗口显示状态"""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def send_message(self):
        """发送消息"""
        message = self.input_var.get().strip()
        if not message:
            return
        
        # 显示用户消息
        self.show_response(f"你: {message}", is_user=True)
        
        # 清空输入框
        self.input_var.set("")
        
        # 调整窗口大小
        self.adjust_window_size()
        
        # 调用AI处理
        if hasattr(self.pet_window, 'ai_handler') and self.pet_window.ai_handler:
            # 在新线程中处理AI响应
            threading.Thread(
                target=self.process_ai_response,
                args=(message,),
                daemon=True
            ).start()
        else:
            self.show_response("小星: AI功能未启用或配置不正确 (╯︵╰,)", is_ai=True)
    
    def process_ai_response(self, message):
        """处理AI响应"""
        # 显示思考中...
        self.show_response("小星: 思考中...", is_ai=True, is_thinking=True)
        
        # 调用AI
        response = self.pet_window.ai_handler.chat(message)
        
        if response:
            self.show_response(f"小星: {response}", is_ai=True)
        else:
            self.show_response("小星: 抱歉，我好像出错了... (╥﹏╥)", is_ai=True)
    
    def show_response(self, text, is_user=False, is_ai=False, is_thinking=False):
        """在响应框中显示消息"""
        # 在主线程中更新UI
        def update_ui():
            self.response_text.config(state=tk.NORMAL)
            
            # 清空之前的思考中消息
            if is_thinking:
                self.response_text.delete(1.0, tk.END)
            
            # 添加新消息
            tag = "user" if is_user else "ai"
            self.response_text.insert(tk.END, text + "\n\n", tag)
            
            # 配置标签样式
            if is_user:
                self.response_text.tag_config("user", foreground="#FF69B4", font=("Microsoft YaHei", 10, "bold"))
            else:
                self.response_text.tag_config("ai", foreground="#4169E1", font=("Microsoft YaHei", 10))
            
            # 滚动到底部
            self.response_text.see(tk.END)
            self.response_text.config(state=tk.DISABLED)
            
            # 如果不是思考中消息，调整窗口大小
            if not is_thinking:
                self.adjust_window_size()
            
            # 设置自动隐藏定时器（长文本给予更多时间阅读）
            text_length = len(text)
            timeout = 30000  # 基础30秒
            if text_length > 200:
                timeout = 45000  # 45秒
            elif text_length > 100:
                timeout = 35000  # 35秒
                
            # 清除之前的定时器
            if hasattr(self, '_clear_timer'):
                self.window.after_cancel(self._clear_timer)
            
            # 设置新的定时器
            self._clear_timer = self.window.after(timeout, self.clear_response)
        
        self.parent.after(0, update_ui)
    
    def clear_response(self):
        """清除响应框内容"""
        def clear_ui():
            self.response_text.config(state=tk.NORMAL)
            self.response_text.delete(1.0, tk.END)
            self.response_text.config(state=tk.DISABLED)
            
            # 重置窗口大小
            self.window_width = self.base_width
            self.window_height = self.base_height
            self.update_position()
        
        self.parent.after(0, clear_ui)


class PetWindow:
    def __init__(self, root):
        self.root = root
        self._request_quit = False  # 退出标志

        # 立即设置无边框，避免闪烁
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.config(bg=TRANSPARENT_COLOR)
        root.attributes("-transparentcolor", TRANSPARENT_COLOR)

        # 加载配置
        config = load_config()
        self.scale_index = config.get("scale_index", 3)
        self.scale = SCALE_OPTIONS[self.scale_index]

        # 加载所有GIF
        self.load_gifs()

        # 当前状态
        self.current_frames = self.move_frames
        self.current_delays = self.move_delays
        self.is_moving = True
        self.is_paused = False
        self.moving_right = True
        self.frame_index = 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self._pre_drag_frames = None
        self._pre_drag_delays = None

        self.screenshot_timer = None
        self.last_screenshot_time = 0
        self.is_analyzing_screenshot = False
        self.last_analysis_result = None
        
        # 启动截图分析定时器
        self.start_screenshot_analysis()


        self.label = tk.Label(root, bg=TRANSPARENT_COLOR, bd=0)
        self.label.pack()

        self.w = self.current_frames[0].width()
        self.h = self.current_frames[0].height()
        self.x = 200
        self.y = 200
        root.geometry(f"{self.w}x{self.h}+{self.x}+{self.y}")

        # 强制刷新，让 winfo_x/y 生效
        root.update_idletasks()

        # 加载配置并设置
        self.click_through = config.get("click_through", True)
        self.follow_mouse = config.get("follow_mouse", False)
        self.set_click_through(self.click_through)

        self.transparency_index = config.get("transparency_index", 0)
        self.set_transparency(self.transparency_index)

        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()

        self.vx = SPEED_X
        self.vy = SPEED_Y

        # 运动系统初始化
        self.target_x, self.target_y = self.get_random_target()
        self.target_timer = random.randint(TARGET_CHANGE_MIN, TARGET_CHANGE_MAX)

        # 状态机变量
        self.motion_state = MOTION_WANDER
        self.rest_timer = 0

        # 绑定拖动事件
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.do_drag)
        self.label.bind("<ButtonRelease-1>", self.stop_drag)
        
        # 绑定右键点击事件 - 切换聊天窗口
        self.label.bind("<ButtonPress-3>", self.toggle_chat_window)

        # 创建聊天窗口
        self.chat_window = ChatWindow(root, self)
        
        # 初始化AI处理器
        self.ai_handler = None
        self.init_ai_handler(config)

        self.animate()
        self.move()

        # 获取窗口句柄
        self.root.update_idletasks()
        self.hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

        # 启动轻量级置顶轮询
        self.root.after(2000, self.ensure_topmost)
        
        # 启动聊天窗口位置更新
        self.root.after(100, self.update_chat_position)

        # 启动退出轮询
        self.root.after(100, self.check_quit)

    def load_gifs(self):
        """加载所有GIF文件"""
        # 加载move.gif
        move_path = resource_path(os.path.join(GIF_DIR, "move.gif"))
        self.move_frames, self.move_delays, self.move_pil_frames = load_gif_frames(
            move_path, self.scale
        )
        # 加载翻转的move帧（向左）
        self.move_frames_left = flip_frames(self.move_pil_frames)

        # 加载idle1~4.gif
        self.idle_gifs = []
        for i in range(1, 5):
            idle_path = resource_path(os.path.join(GIF_DIR, f"idle{i}.gif"))
            frames, delays, _ = load_gif_frames(idle_path, self.scale)
            self.idle_gifs.append((frames, delays))

        # 加载drag.gif
        drag_path = resource_path(os.path.join(GIF_DIR, "drag.gif"))
        self.drag_frames, self.drag_delays, _ = load_gif_frames(drag_path, self.scale)
        
        # 加载聊天图标（在move.gif右侧添加输入框图标）
        try:
            # 创建一个简单的聊天图标
            chat_icon = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
            # 这里可以添加绘制聊天气泡的代码
            # 暂时留空，后续可以自定义
            self.chat_icon = ImageTk.PhotoImage(chat_icon)
        except:
            self.chat_icon = None

    def init_ai_handler(self, config):
        """初始化AI处理器"""
        try:
            from ai_handler import AIChatHandler, ConfigManager
            
            # 加载AI配置
            ai_config_manager = ConfigManager()
            api_key = ai_config_manager.get_api_key()
            ai_enabled = ai_config_manager.get_enable_ai()
            
            # 如果配置文件中有API密钥，优先使用
            if not api_key and "api_key" in config:
                api_key = config["api_key"]
            
            if api_key and (ai_enabled or config.get("ai_enabled", False)):
                self.ai_handler = AIChatHandler(api_key=api_key, config_manager=ai_config_manager)  # 传入config_manager

                print("AI处理器初始化成功")
                
                # 加载截图分析配置
                self.enable_screenshot_analysis = ai_config_manager.get_enable_screenshot_analysis()
                self.screenshot_interval = ai_config_manager.get_screenshot_interval()
                self.only_analyze_when_idle = ai_config_manager.get_only_analyze_when_idle()
                
                # 获取温度和token设置
                self.ai_temperature = ai_config_manager.get_temperature()
                self.ai_max_tokens = ai_config_manager.get_max_tokens()
            else:
                print("AI功能未启用或API密钥未配置")
                self.enable_screenshot_analysis = False
        except ImportError as e:
            print(f"无法导入ai_handler模块: {e}")
        except Exception as e:
            print(f"初始化AI处理器失败: {e}")


    def start_screenshot_analysis(self):
        """启动截图分析定时器"""
        if self.screenshot_timer:
            self.root.after_cancel(self.screenshot_timer)
        
        # 检查是否启用截图分析
        if not hasattr(self, 'enable_screenshot_analysis') or not self.enable_screenshot_analysis:
            return
        
        current_time = time.time()
        interval_ms = self.screenshot_interval * 1000
        
        # 每60秒检查一次（可在配置中调整）
        if current_time - self.last_screenshot_time >= self.screenshot_interval:
            # 检查条件：AI处理器已初始化且未在分析中
            if (self.ai_handler and not self.is_analyzing_screenshot and 
                not self.chat_window.visible and not self.is_paused):
                
                # 检查是否仅在空闲时分析
                if self.only_analyze_when_idle and self.motion_state != MOTION_REST:
                    pass  # 宠物在运动，跳过分析
                else:
                    # 在新线程中进行分析
                    threading.Thread(
                        target=self.analyze_screenshot_and_chat,
                        daemon=True
                    ).start()
            
            self.last_screenshot_time = current_time
        
        # 设置下一次检查
        self.screenshot_timer = self.root.after(interval_ms, self.start_screenshot_analysis)

    def analyze_screenshot_and_chat(self):
        """截图分析并自动发起话题"""
        if not self.ai_handler or self.is_analyzing_screenshot:
            return
        
        self.is_analyzing_screenshot = True
        
        try:
            # 让AI分析截图
            analysis_result = self.ai_handler.analyze_screenshot(
                "用户正在做什么？根据截图内容，分析用户可能在做什么工作或活动。"
            )
            
            if analysis_result:
                # 保存分析结果
                self.last_analysis_result = analysis_result
                
                # 在主线程中显示分析结果
                self.root.after(0, lambda: self.show_analysis_result(analysis_result))
                
                print(f"截图分析结果: {analysis_result[:50]}...")
            else:
                print("截图分析失败")
                
        except Exception as e:
            print(f"截图分析出错: {e}")
        finally:
            self.is_analyzing_screenshot = False

    def show_analysis_result(self, analysis_result):
        """显示截图分析结果"""
        # 只在聊天窗口未显示时才显示
        if not self.chat_window.visible:
            # 暂停宠物移动
            was_paused = self.is_paused
            if not was_paused:
                self.toggle_pause()
            
            # 显示聊天窗口
            self.chat_window.show()
            
            # 在聊天窗口中显示分析结果
            self.chat_window.show_response(
                f"小星: （刚刚偷偷观察了一下你的屏幕~）\n\n{analysis_result}\n\n要和我聊聊这个吗？ (◕‿◕✿)",
                is_ai=True
            )
            
            # 3分钟后如果没有互动，自动关闭聊天窗口
            self.root.after(180000, self.auto_close_chat_if_idle)

    def auto_close_chat_if_idle(self):
        """如果聊天窗口空闲，自动关闭"""
        if self.chat_window.visible:
            # 获取聊天历史，检查是否有新消息
            if hasattr(self.chat_window, 'response_text'):
                current_content = self.chat_window.response_text.get(1.0, tk.END).strip()
                # 如果内容仍然是自动分析的结果，说明用户没有互动
                if "刚刚偷偷观察了一下你的屏幕" in current_content:
                    self.chat_window.hide()
                    # 如果之前不是暂停状态，恢复移动
                    if self.is_paused:
                        self.toggle_pause()

    def toggle_chat_window(self, event=None):
        """切换聊天窗口显示/隐藏"""
        self.chat_window.toggle()
        
        self.toggle_pause()
            
            # 如果有上次的分析结果，可以显示
        if self.last_analysis_result and not event:
            self.root.after(500, lambda: self.chat_window.show_response(
                f"小星: 上次我发现你在{self.last_analysis_result[:50]}...\n想继续聊这个话题吗？",
                is_ai=True
            ))
    
    def update_chat_position(self):
        """更新聊天窗口位置"""
        if self.chat_window.visible:
            self.chat_window.update_position()
        
        # 继续更新位置
        self.root.after(100, self.update_chat_position)

    def ensure_topmost(self):
        """轻量级置顶轮询"""
        if not self.is_paused:
            try:
                ctypes.windll.user32.SetWindowPos(
                    self.hwnd,
                    HWND_TOPMOST,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
                )
            except:
                pass
        self.root.after(2000, self.ensure_topmost)

    def check_quit(self):
        """主线程轮询退出标志"""
        if self._request_quit:
            try:
                if hasattr(self, "app") and self.app:
                    self.app.stop()
            except:
                pass
            self.root.destroy()
            return
        self.root.after(100, self.check_quit)

    def set_click_through(self, enable):
        """设置鼠标穿透"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enable:
                ctypes.windll.user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                )
            else:
                ctypes.windll.user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT
                )
        except Exception as e:
            print(f"设置鼠标穿透失败: {e}")

    def set_transparency(self, index):
        """设置透明度"""
        self.transparency_index = index
        alpha = TRANSPARENCY_OPTIONS[index]
        self.root.attributes("-alpha", alpha)
        # 保存配置
        config = load_config()
        config["transparency_index"] = index
        save_config(config)

    def stop_drag(self, event):
        """停止拖动"""
        self.dragging = False
        # 恢复拖动前的帧
        if self._pre_drag_frames is not None:
            self.current_frames = self._pre_drag_frames
            self.current_delays = self._pre_drag_delays
            self.frame_index = 0

    def set_scale(self, index):
        """设置缩放"""
        self.scale_index = index
        self.scale = SCALE_OPTIONS[index]
        config = load_config()
        config["scale_index"] = index
        save_config(config)

        # 重新加载GIF
        self.load_gifs()

        # 更新窗口大小
        if self.move_frames:
            self.w = self.move_frames[0].width()
            self.h = self.move_frames[0].height()
            self.root.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

        # 重置帧索引，切换到move帧
        self.frame_index = 0
        self.current_frames = (
            self.move_frames if self.moving_right else self.move_frames_left
        )
        self.current_delays = self.move_delays

    def toggle_pause(self):
        """切换暂停/继续"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            # 暂停：停止移动，切换到idle动画
            self.is_moving = False
            frames, delays = random.choice(self.idle_gifs)
            self.current_frames = frames
            self.current_delays = delays
            self.frame_index = 0
        else:
            # 继续：恢复移动
            self.is_moving = True
            self.current_frames = (
                self.move_frames if self.moving_right else self.move_frames_left
            )
            self.current_delays = self.move_delays
            self.frame_index = 0

    def start_drag(self, event):
        """开始拖动（鼠标穿透关闭时才可用）"""
        if self.click_through:
            return
        self.dragging = True
        # 记录鼠标相对于窗口左上角的偏移量
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        # 保存当前帧状态
        self._pre_drag_frames = self.current_frames
        self._pre_drag_delays = self.current_delays
        # 切换到drag静态帧（只显示第一帧）
        self.current_frames = self.drag_frames
        self.current_delays = [1000] * len(self.drag_frames)
        self.frame_index = 0
        self.label.config(image=self.current_frames[0])

    def do_drag(self, event):
        """拖动中"""
        if self.dragging:
            # 窗口左上角 = 鼠标当前位置 - 偏移量
            self.x = event.x_root - self.drag_start_x
            self.y = event.y_root - self.drag_start_y
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def switch_to_idle(self):
        """切换到随机idle状态（随机停下功能）"""
        if self.is_paused:
            return

        # 有一定概率直接停在原地，不播放动画
        if random.random() < STAY_PUT_CHANCE:
            # 停在原地：关闭移动，但不播放 idle 动画
            self.is_moving = False
            # 停止一段时间后恢复移动
            stop_duration = random.randint(STOP_DURATION_MIN, STOP_DURATION_MAX)
            self.root.after(stop_duration, self.switch_to_move)
        else:
            # 播放 idle 动画
            self.is_moving = False
            frames, delays = random.choice(self.idle_gifs)
            self.current_frames = frames
            self.current_delays = delays
            self.frame_index = 0
            # 随机停止一段时间后恢复移动
            stop_duration = random.randint(STOP_DURATION_MIN, STOP_DURATION_MAX)
            self.root.after(stop_duration, self.switch_to_move)

    def switch_to_move(self):
        """切换到移动状态"""
        if self.is_paused:
            return
        self.is_moving = True
        self.current_frames = (
            self.move_frames if self.moving_right else self.move_frames_left
        )
        self.current_delays = self.move_delays
        self.frame_index = 0

    # ============ 运动系统方法 ============

    def get_random_target(self):
        """获取随机目标点（偶尔在屏幕外，触发边缘效果）"""
        if random.random() < OUTSIDE_TARGET_CHANCE:
            side = random.choice(["left", "right", "top", "bottom"])
            margin = RESPAWN_MARGIN + 50
            if side == "left":
                return (-margin, random.randint(0, self.screen_h - self.h))
            elif side == "right":
                return (
                    self.screen_w + margin,
                    random.randint(0, self.screen_h - self.h),
                )
            elif side == "top":
                return (random.randint(0, self.screen_w - self.w), -margin)
            else:  # bottom
                return (
                    random.randint(0, self.screen_w - self.w),
                    self.screen_h + margin,
                )
        else:
            return (
                random.randint(0, self.screen_w - self.w),
                random.randint(0, self.screen_h - self.h),
            )

    def respawn_from_edge(self):
        """从屏幕边缘外侧重生"""
        side = random.choice(["left", "right", "top", "bottom"])
        if side == "left":
            self.x = -RESPAWN_MARGIN
            self.y = random.randint(0, self.screen_h - self.h)
        elif side == "right":
            self.x = self.screen_w + RESPAWN_MARGIN
            self.y = random.randint(0, self.screen_h - self.h)
        elif side == "top":
            self.y = -RESPAWN_MARGIN
            self.x = random.randint(0, self.screen_w - self.w)
        else:  # bottom
            self.y = self.screen_h + RESPAWN_MARGIN
            self.x = random.randint(0, self.screen_w - self.w)

        # 给一点入场速度
        self.vx = random.choice([-3, 3])
        self.vy = random.randint(-2, 2)

    def handle_edge(self):
        """处理边缘：反弹或出屏重生"""
        escaped = False

        # 检测是否出屏
        if self.x < -self.w or self.x > self.screen_w:
            escaped = True
        if self.y < -self.h or self.y > self.screen_h:
            escaped = True

        if escaped:
            if random.random() < EDGE_ESCAPE_CHANCE:
                self.respawn_from_edge()
                return True
            else:
                # 反弹
                self.vx = -self.vx
                self.vy = -self.vy
                # 拉回屏幕内
                self.x = max(0, min(self.screen_w - self.w, self.x))
                self.y = max(0, min(self.screen_h - self.h, self.y))
        return False

    # ============ 动画方法 ============

    def animate(self):
        if not self.current_frames:
            self.root.after(100, self.animate)
            return
        # 拖动时不更新帧（静态显示）
        if self.dragging:
            self.root.after(50, self.animate)
            return
        self.label.config(image=self.current_frames[self.frame_index])
        delay = self.current_delays[self.frame_index] if self.current_delays else 100

        self.frame_index = (self.frame_index + 1) % len(self.current_frames)
        self.root.after(delay, self.animate)

    def move(self):
        """运动状态机主循环（性能优化版）"""
        # 暂停时停止所有运动
        if self.is_paused:
            self.root.after(100, self.move)
            return

        # 拖动时停止自动运动
        if self.dragging:
            self.root.after(50, self.move)
            return

        # ============ 随机停下休息（游荡模式专属） ============
        if self.motion_state == MOTION_WANDER and self.is_moving:
            if random.random() < STOP_CHANCE:
                self.switch_to_idle()
                self.root.after(MOVE_INTERVAL, self.move)
                return

        # ============ 休息状态 ============
        if self.motion_state == MOTION_REST:
            self.rest_timer -= MOVE_INTERVAL
            if self.rest_timer <= 0:
                # 休息结束，恢复游荡
                self.motion_state = MOTION_WANDER
                self.target_x, self.target_y = self.get_random_target()
                self.target_timer = random.randint(TARGET_CHANGE_MIN, TARGET_CHANGE_MAX)
                self.switch_to_move()
            self.root.after(MOVE_INTERVAL, self.move)
            return

        # ============ 鼠标位置缓存 ============
        mx = self.root.winfo_pointerx()
        my = self.root.winfo_pointery()
        mouse_moved = (mx, my) != getattr(self, "_last_mouse", (mx, my))
        self._last_mouse = (mx, my)

        # ============ 计算到目标的距离 ============
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        # ============ 状态判断与切换 ============

        # 如果关闭了跟随模式，强制重置为游荡模式
        if not self.follow_mouse and self.motion_state in (
            MOTION_FOLLOW,
            MOTION_CURIOUS,
        ):
            self.motion_state = MOTION_WANDER

        # 跟随模式：根据距离切换follow/curious
        if self.follow_mouse:
            dist_mouse = ((mx - self.x) ** 2 + (my - self.y) ** 2) ** 0.5

            if dist_mouse > FOLLOW_START_DIST:
                self.motion_state = MOTION_FOLLOW
            elif dist_mouse < FOLLOW_STOP_DIST:
                self.motion_state = MOTION_CURIOUS

        # 游荡模式：到达目标后决定是否休息
        elif self.motion_state == MOTION_WANDER and dist < REST_DISTANCE:
            if random.random() < REST_CHANCE:
                # 休息一下
                self.motion_state = MOTION_REST
                self.rest_timer = random.randint(REST_DURATION_MIN, REST_DURATION_MAX)
                self.switch_to_idle()
                self.root.after(MOVE_INTERVAL, self.move)
                return
            else:
                # 继续游荡，换个目标
                self.target_x, self.target_y = self.get_random_target()
                self.target_timer = random.randint(TARGET_CHANGE_MIN, TARGET_CHANGE_MAX)

        # ============ 定时更换目标（仅游荡模式） ============
        if self.motion_state == MOTION_WANDER:
            self.target_timer -= 1
            if self.target_timer <= 0:
                self.target_x, self.target_y = self.get_random_target()
                self.target_timer = random.randint(TARGET_CHANGE_MIN, TARGET_CHANGE_MAX)

        # ============ 计算速度倍率 ============
        if self.motion_state == MOTION_WANDER:
            speed_mul = SPEED_WANDER
        elif self.motion_state == MOTION_FOLLOW:
            speed_mul = SPEED_FOLLOW
        elif self.motion_state == MOTION_CURIOUS:
            speed_mul = SPEED_CURIOUS
        else:
            speed_mul = 1.0

        # ============ 跟随/好奇模式：只在鼠标移动时更新目标 ============
        if self.motion_state in (MOTION_FOLLOW, MOTION_CURIOUS):
            if mouse_moved:  # 只有鼠标移动时才更新目标
                if self.motion_state == MOTION_FOLLOW:
                    offset = FOLLOW_DISTANCE
                else:  # curious
                    offset = FOLLOW_STOP_DIST
                self.target_x = mx + random.randint(-offset, offset)
                self.target_y = my + random.randint(-offset, offset)

                # 重新计算距离
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                dist = max(1, (dx * dx + dy * dy) ** 0.5)

        # ============ 朝目标移动（惯性 + 意图） ============
        desired_vx = dx / dist * SPEED_X * speed_mul
        desired_vy = dy / dist * SPEED_Y * speed_mul

        # 惯性融合
        self.vx = self.vx * INERTIA_FACTOR + desired_vx * INTENT_FACTOR
        self.vy = self.vy * INERTIA_FACTOR + desired_vy * INTENT_FACTOR

        # ============ 抖动降频：每N帧更新一次 ============
        if not hasattr(self, "_move_tick"):
            self._move_tick = 0
        self._move_tick += 1

        if self._move_tick % JITTER_INTERVAL == 0:
            self._jitter_x = random.uniform(-JITTER, JITTER)
            self._jitter_y = random.uniform(-JITTER, JITTER)
        self.vx += getattr(self, "_jitter_x", 0)
        self.vy += getattr(self, "_jitter_y", 0)

        # 应用移动
        self.x += self.vx
        self.y += self.vy

        # ============ 边缘处理 ============
        if not self.handle_edge():
            # 没出屏时才检查边界碰撞
            hit_edge = False
            if self.x <= 0:
                self.x = 0
                self.vx = abs(self.vx)  # 向右反弹
                hit_edge = True
            elif self.x + self.w >= self.screen_w:
                self.x = self.screen_w - self.w
                self.vx = -abs(self.vx)  # 向左反弹
                hit_edge = True

            if self.y <= 0:
                self.y = 0
                self.vy = abs(self.vy)  # 向下
                hit_edge = True
            elif self.y + self.h >= self.screen_h:
                self.y = self.screen_h - self.h
                self.vy = -abs(self.vy)  # 向上
                hit_edge = True

            # 撞边时更新方向状态
            new_moving_right = self.vx > 0.5
            new_moving_left = self.vx < -0.5

            if new_moving_right and not self.moving_right:
                self.moving_right = True
                self.current_frames = self.move_frames
                self.current_delays = self.move_delays
                self.frame_index = 0
            elif new_moving_left and self.moving_right:
                self.moving_right = False
                self.current_frames = self.move_frames_left
                self.current_delays = self.move_delays
                self.frame_index = 0

        # 只在位置明显变化时更新geometry
        ix, iy = int(self.x), int(self.y)
        last_pos = getattr(self, "_last_pos", None)
        if (ix, iy) != last_pos:
            self.root.geometry(f"+{ix}+{iy}")
            self._last_pos = (ix, iy)

        self.root.after(MOVE_INTERVAL, self.move)