# ai_param_style.py - AI参数调节样式
"""
AI参数调节组件的样式配置
"""

# 温度参数预设
TEMPERATURE_PRESETS = [
    {"value": 0.0, "label": "完全确定", "desc": "回复完全一致，适合正式场合"},
    {"value": 0.3, "label": "保守", "desc": "回复比较一致，略微变化"},
    {"value": 0.7, "label": "平衡", "desc": "回复有变化，但不过分随机"},
    {"value": 1.0, "label": "创意", "desc": "回复比较随机，有创意"},
    {"value": 1.5, "label": "非常创意", "desc": "回复非常随机，有创造性"},
    {"value": 2.0, "label": "天马行空", "desc": "回复极其随机，不可预测"},
]

# Max Tokens预设
TOKENS_PRESETS = [
    {"value": 100, "label": "简短", "desc": "非常简短的回复"},
    {"value": 300, "label": "简洁", "desc": "简洁明了的回复"},
    {"value": 500, "label": "适中", "desc": "标准长度的回复"},
    {"value": 1000, "label": "详细", "desc": "比较详细的回复"},
    {"value": 2000, "label": "非常详细", "desc": "非常详细的回复"},
    {"value": 4000, "label": "详尽", "desc": "详尽完整的回复"},
]

def create_parameter_scale(parent, title, var, from_val, to_val, resolution, update_callback=None):
    """创建参数调节滑动条"""
    frame = tk.Frame(parent, bg='white')
    
    # 标题
    tk.Label(
        frame,
        text=title,
        font=("Microsoft YaHei UI", 10),
        bg='white',
        fg='#333333'
    ).pack(anchor=tk.W)
    
    # 滑动条容器
    scale_frame = tk.Frame(frame, bg='white')
    scale_frame.pack(fill=tk.X, pady=(8, 0))
    
    # 最小值标签
    tk.Label(
        scale_frame,
        text=str(from_val),
        font=("Microsoft YaHei UI", 9),
        bg='white',
        fg='#666666'
    ).pack(side=tk.LEFT)
    
    # 滑动条
    scale = tk.Scale(
        scale_frame,
        from_=from_val,
        to=to_val,
        resolution=resolution,
        variable=var,
        orient=tk.HORIZONTAL,
        length=280,
        showvalue=False,
        bg='white',
        fg='#333333',
        troughcolor='#FFF5F7',
        activebackground='#FFB6C1',
        highlightthickness=0,
        sliderrelief=tk.FLAT,
        command=update_callback
    )
    scale.pack(side=tk.LEFT, padx=10)
    
    # 最大值标签
    tk.Label(
        scale_frame,
        text=str(to_val),
        font=("Microsoft YaHei UI", 9),
        bg='white',
        fg='#666666'
    ).pack(side=tk.LEFT)
    
    # 当前值显示
    value_frame = tk.Frame(frame, bg='white')
    value_frame.pack(pady=(10, 0))
    
    value_label = tk.Label(
        value_frame,
        text=str(var.get()),
        font=("Microsoft YaHei UI", 12, "bold"),
        bg='white',
        fg='#FF69B4'
    )
    value_label.pack(side=tk.LEFT)
    
    # 描述标签
    desc_label = tk.Label(
        value_frame,
        text="",
        font=("Microsoft YaHei UI", 9),
        bg='white',
        fg='#666666'
    )
    desc_label.pack(side=tk.LEFT, padx=(10, 0))
    
    return frame, value_label, desc_label, scale

def create_preset_buttons(parent, presets, current_value, callback):
    """创建预设按钮"""
    button_frame = tk.Frame(parent, bg='white')
    
    for preset in presets:
        btn = tk.Button(
            button_frame,
            text=preset["label"],
            font=("Microsoft YaHei UI", 8),
            relief=tk.FLAT,
            bg='#FFF5F7' if current_value != preset["value"] else '#FF69B4',
            fg='#333333' if current_value != preset["value"] else 'white',
            padx=10,
            pady=2,
            command=lambda v=preset["value"], l=preset["label"], d=preset["desc"]: callback(v, l, d)
        )
        btn.pack(side=tk.LEFT, padx=2)
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#FFB6C1'))
        btn.bind("<Leave>", lambda e, b=btn, v=preset["value"], cv=current_value: 
                b.config(bg='#FF69B4' if cv == v else '#FFF5F7'))
    
    return button_frame