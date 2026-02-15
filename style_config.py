# style_config.py - 样式配置
"""
桌面宠物聊天窗口样式配置
"""

# 颜色配置
COLORS = {
    'primary_pink': '#FF69B4',
    'dark_pink': '#FF1493',
    'light_pink': '#FFB6C1',
    'pale_pink': '#FFF5F7',
    'white': '#FFFFFF',
    'text_dark': '#333333',
    'text_gray': '#666666',
    'ai_blue': '#4169E1',
    'error_red': '#FF4444',
}

# 字体配置
FONTS = {
    'title': ('Microsoft YaHei UI', 14, 'bold'),
    'subtitle': ('Microsoft YaHei UI', 12, 'bold'),
    'body': ('Microsoft YaHei UI', 10),
    'small': ('Microsoft YaHei UI', 8),
    'chat_input': ('Microsoft YaHei', 10),
    'chat_response': ('Microsoft YaHei', 10),
}

# 窗口尺寸配置
WINDOW_SIZES = {
    'chat_base_width': 280,
    'chat_base_height': 180,
    'chat_max_width': 400,
    'chat_max_height': 400,
    'chat_min_width': 250,
    'chat_min_height': 120,
    'config_width': 450,
    'config_height': 350,
}

# 动画配置
ANIMATION = {
    'hover_color': '#FF1493',  # 悬停颜色
    'normal_color': '#FF69B4',  # 正常颜色
    'transition_ms': 150,  # 过渡时间
}

def create_rounded_button(canvas, x, y, width, height, text, **kwargs):
    """
    创建圆角矩形按钮
    
    Args:
        canvas: tkinter Canvas对象
        x, y: 中心坐标
        width, height: 按钮尺寸
        text: 按钮文本
        **kwargs: 其他参数（颜色、字体等）
    """
    radius = min(width, height) // 4
    
    # 默认参数
    bg_color = kwargs.get('bg_color', COLORS['primary_pink'])
    fg_color = kwargs.get('fg_color', COLORS['white'])
    border_color = kwargs.get('border_color', COLORS['dark_pink'])
    border_width = kwargs.get('border_width', 2)
    font = kwargs.get('font', FONTS['body'])
    
    # 计算坐标
    x1, y1 = x - width // 2, y - height // 2
    x2, y2 = x + width // 2, y + height // 2
    
    # 创建圆角矩形
    button_id = canvas.create_round_rectangle(
        x1, y1, x2, y2, radius, 
        fill=bg_color, outline=border_color, width=border_width
    )
    
    # 创建文本
    text_id = canvas.create_text(x, y, text=text, fill=fg_color, font=font)
    
    return button_id, text_id

# 为Canvas添加创建圆角矩形的方法
def add_rounded_rectangle_to_canvas():
    """为tkinter Canvas添加创建圆角矩形的方法"""
    import tkinter as tk
    
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """
        在Canvas上创建圆角矩形
        
        Args:
            x1, y1: 左上角坐标
            x2, y2: 右下角坐标
            radius: 圆角半径
            **kwargs: 其他Canvas参数
        """
        points = []
        
        # 左上角
        points.append(x1 + radius)
        points.append(y1)
        points.append(x2 - radius)
        points.append(y1)
        
        # 右上角
        points.append(x2)
        points.append(y1)
        points.append(x2)
        points.append(y1 + radius)
        
        points.append(x2)
        points.append(y1 + radius)
        points.append(x2)
        points.append(y2 - radius)
        
        # 右下角
        points.append(x2)
        points.append(y2)
        points.append(x2 - radius)
        points.append(y2)
        
        points.append(x2 - radius)
        points.append(y2)
        points.append(x1 + radius)
        points.append(y2)
        
        # 左下角
        points.append(x1)
        points.append(y2)
        points.append(x1)
        points.append(y2 - radius)
        
        points.append(x1)
        points.append(y2 - radius)
        points.append(x1)
        points.append(y1 + radius)
        
        # 左上角闭合
        points.append(x1)
        points.append(y1)
        points.append(x1 + radius)
        points.append(y1)
        
        return self.create_polygon(points, **kwargs, smooth=True)
    
    # 将方法添加到Canvas类
    tk.Canvas.create_round_rectangle = _create_rounded_rectangle

# 初始化时调用
add_rounded_rectangle_to_canvas()