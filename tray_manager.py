import pystray
from PIL import Image as PILImage, Image
import tkinter as tk
from PIL import ImageTk
import webbrowser

def create_tray_manager(app, root):
    """创建托盘管理器"""
    # 创建托盘图标（使用ameath.gif）
    try:
        icon_gif = Image.open("gifs/ameath.gif")
        icon_gif.seek(0)  # 取第一帧
        icon_image = icon_gif.convert("RGBA")
        icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"加载托盘图标失败，使用默认图标: {e}")
        icon_image = PILImage.new("RGB", (64, 64), color="pink")

    # 定义事件处理函数
    def on_toggle_visible(icon, item):
        """切换隐藏/显示"""
        if app.root.state() == "withdrawn":
            app.root.deiconify()
        else:
            app.root.withdraw()

    def on_toggle_pause(icon, item):
        """切换暂停/继续"""
        app.toggle_pause()

    def on_toggle_chat(icon, item):
        """切换聊天窗口"""
        app.toggle_chat_window()

    def on_toggle_screenshot_analysis(icon, item):
        """切换截图分析"""
        try:
            from ai_handler import ConfigManager
            from pet_window import load_config, save_config
            
            ai_config = ConfigManager()
            current = ai_config.get_enable_screenshot_analysis()
            ai_config.set_enable_screenshot_analysis(not current)
            
            # 更新应用状态
            if hasattr(app, 'enable_screenshot_analysis'):
                app.enable_screenshot_analysis = not current
                
            # 重启定时器
            if hasattr(app, 'start_screenshot_analysis'):
                app.start_screenshot_analysis()
                
        except Exception as e:
            print(f"切换截图分析失败: {e}")

    def on_quit(icon):
        """退出"""
        app._request_quit = True

    def on_toggle_click_through(icon, item):
        """切换鼠标穿透"""
        from pet_window import load_config, save_config
        
        app.click_through = not app.click_through
        app.set_click_through(app.click_through)
        config = load_config()
        config["click_through"] = app.click_through
        save_config(config)

    def on_toggle_follow(icon, item):
        """切换跟随鼠标"""
        from pet_window import load_config, save_config
        
        app.follow_mouse = not app.follow_mouse
        config = load_config()
        config["follow_mouse"] = app.follow_mouse
        save_config(config)

    def on_configure_ai(icon, item):
        """配置AI设置"""
        try:
            from ai_handler import ConfigManager
            from pet_window import load_config, save_config
        
            # 创建配置窗口
            config_window = tk.Toplevel(app.root)
            config_window.title("AI配置")
            config_window.geometry("520x550")  # 增加宽度以容纳滚动条
            config_window.resizable(False, False)
            config_window.attributes("-topmost", True)
            config_window.configure(bg='#FFB6C1')
        
            # 创建带滚动条的主容器
            main_container = tk.Frame(config_window, bg='#FFB6C1')
            main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
            # 创建Canvas和滚动条
            canvas = tk.Canvas(main_container, bg='#FFB6C1', highlightthickness=0)
            scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
            # 滚动区域
            scrollable_frame = tk.Frame(canvas, bg='#FFB6C1')
        
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
        
            # 将滚动区域添加到Canvas
            canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
            # 配置Canvas的滚动
            canvas.configure(yscrollcommand=scrollbar.set)
        
            # 绑定鼠标滚轮事件
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
            def _on_enter(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
            def _on_leave(event):
                canvas.unbind_all("<MouseWheel>")
        
            canvas.bind("<Enter>", _on_enter)
            canvas.bind("<Leave>", _on_leave)
        
            # 网格布局以自适应宽度
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
        
            main_container.grid_rowconfigure(0, weight=1)
            main_container.grid_columnconfigure(0, weight=1)
        
            # 确保滚动区域宽度自适应
            def configure_scrollable_frame(event):
                canvas.itemconfig(canvas_window, width=event.width)
        
            canvas.bind("<Configure>", configure_scrollable_frame)
        
            # 创建主容器，带粉色边框
            main_frame = tk.Frame(scrollable_frame, bg='#FFB6C1', bd=3, relief=tk.RAISED)
            main_frame.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)
        
            # 内容区域
            content_frame = tk.Frame(main_frame, bg='white')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
            # 标题
            title_frame = tk.Frame(content_frame, bg='white')
            title_frame.pack(fill=tk.X, pady=(15, 10))
        
            tk.Label(
                title_frame,
                text="AI聊天配置",
                font=("Microsoft YaHei UI", 14, "bold"),
                fg='#FF69B4',
                bg='white'
            ).pack()
        
            # 配置区域
            config_area = tk.Frame(content_frame, bg='white', padx=20)
            config_area.pack(fill=tk.BOTH, expand=True)
        
            # AI配置管理器
            ai_config = ConfigManager()
            config = load_config()
        
            # API密钥输入
            tk.Label(
                config_area,
                text="DeepSeek API密钥:",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333'
            ).pack(anchor=tk.W, pady=(0, 5))

            api_key_var = tk.StringVar(value=ai_config.get_api_key() or config.get("api_key", ""))
            api_key_entry = tk.Entry(
                config_area,
                textvariable=api_key_var,
                font=("Microsoft YaHei UI", 10),
                width=40,
                show="*",
                relief=tk.FLAT,
                bg='#FFF5F7',
                borderwidth=2,
                highlightthickness=1,
                highlightcolor='#FFB6C1',
                highlightbackground='#FFB6C1'
            )
            api_key_entry.pack(anchor=tk.W, pady=(0, 15))
        
            # API密钥获取提示
            help_label = tk.Label(
                config_area,
                text="可在DeepSeek官网获取API密钥",
                font=("Microsoft YaHei UI", 8),
                fg='#666666',
                bg='white',
                cursor='hand2'
            )
            help_label.pack(anchor=tk.W, pady=(0, 20))
            help_label.bind('<Button-1>', lambda e: webbrowser.open('https://platform.deepseek.com/api_keys'))
        
            # 启用AI复选框
            ai_enabled_var = tk.BooleanVar(value=ai_config.get_enable_ai() or config.get("ai_enabled", False))
        
            # 创建自定义样式的复选框
            def toggle_checkbox():
                current = ai_enabled_var.get()
                ai_enabled_var.set(not current)
                update_checkbox_display()
        
            def update_checkbox_display():
                if ai_enabled_var.get():
                    checkbox_canvas.itemconfig(checkbox_bg, fill='#FF69B4')
                    checkbox_canvas.itemconfig(checkbox_check, text="✓")
                else:
                    checkbox_canvas.itemconfig(checkbox_bg, fill='white')
                    checkbox_canvas.itemconfig(checkbox_check, text="")
        
            checkbox_frame = tk.Frame(config_area, bg='white')
            checkbox_frame.pack(anchor=tk.W, pady=(0, 20))
        
            # 复选框画布
            checkbox_canvas = tk.Canvas(
                checkbox_frame,
                width=20,
                height=20,
                bg='white',
                highlightthickness=0
            )
            checkbox_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
            # 复选框背景和边框
            checkbox_bg = checkbox_canvas.create_rectangle(
                2, 2, 18, 18,
                fill='white' if not ai_enabled_var.get() else '#FF69B4',
                outline='#FF69B4',
                width=2
            )
        
            # 复选框对勾
            checkbox_check = checkbox_canvas.create_text(
                10, 10,
                text="✓" if ai_enabled_var.get() else "",
                font=("Microsoft YaHei UI", 12, "bold"),
                fill='white'
            )
        
            checkbox_canvas.bind("<Button-1>", lambda e: toggle_checkbox())
            checkbox_canvas.config(cursor='hand2')
        
            tk.Label(
                checkbox_frame,
                text="启用AI聊天功能",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333',
                cursor='hand2'
            ).pack(side=tk.LEFT)
            checkbox_frame.bind("<Button-1>", lambda e: toggle_checkbox())
        
            # 分隔线
            separator = tk.Frame(config_area, height=1, bg='#FFB6C1')
            separator.pack(fill=tk.X, pady=(10, 15))
        
            # AI参数调节部分
            tk.Label(
                config_area,
                text="AI参数调节",
                font=("Microsoft YaHei UI", 12, "bold"),
                fg='#FF69B4',
                bg='white'
            ).pack(anchor=tk.W, pady=(0, 15))
        
            # Temperature调节
            temperature_frame = tk.Frame(config_area, bg='white')
            temperature_frame.pack(fill=tk.X, pady=(0, 15))
        
            tk.Label(
                temperature_frame,
                text="随机性 (Temperature):",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333'
            ).pack(anchor=tk.W)
        
            # Temperature值显示和调节
            temperature_var = tk.DoubleVar(value=ai_config.get_temperature())
        
            def update_temperature_label(value):
                """更新temperature标签显示"""
                temp_value = float(value)
                temperature_label.config(text=f"{temp_value:.2f}")
                # 根据值显示说明
                if temp_value < 0.3:
                    description = "（保守，回复一致）"
                elif temp_value < 0.7:
                    description = "（适中，平衡）"
                elif temp_value < 1.0:
                    description = "（有创意，多变）"
                else:
                    description = "（非常随机，有创造性）"
                temp_description.config(text=description)
        
            # Temperature调节控件
            temperature_scale_frame = tk.Frame(temperature_frame, bg='white')
            temperature_scale_frame.pack(fill=tk.X, pady=(5, 0))
        
            # 最小值标签
            tk.Label(
                temperature_scale_frame,
                text="0.0",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            ).pack(side=tk.LEFT)
        
            # 滑动条
            temperature_scale = tk.Scale(
                temperature_scale_frame,
                from_=0.0,
                to=2.0,
                resolution=0.1,
                variable=temperature_var,
                orient=tk.HORIZONTAL,
                length=280,
                showvalue=False,
                bg='white',
                fg='#333333',
                troughcolor='#FFF5F7',
                highlightthickness=0,
                sliderrelief=tk.FLAT,
                command=update_temperature_label
            )
            temperature_scale.pack(side=tk.LEFT, padx=10)
        
            # 最大值标签
            tk.Label(
                temperature_scale_frame,
                text="2.0",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            ).pack(side=tk.LEFT)
        
            # Temperature预设按钮
            temperature_presets_frame = tk.Frame(temperature_frame, bg='white')
            temperature_presets_frame.pack(anchor=tk.W, pady=(5, 0))
        
            temperature_presets = [
                (0.0, "完全确定"),
                (0.3, "保守"),
                (0.7, "平衡"),
                (1.0, "创意"),
                (1.5, "非常创意"),
                (2.0, "天马行空")
            ]
        
            for temp_value, temp_label in temperature_presets:
                def create_temp_preset_handler(val, label):
                    def handler():
                        temperature_var.set(val)
                        update_temperature_label(val)
                    return handler
            
                preset_btn = tk.Button(
                    temperature_presets_frame,
                    text=temp_label,
                    font=("Microsoft YaHei UI", 8),
                    relief=tk.FLAT,
                    bg='#FFF5F7' if temperature_var.get() != temp_value else '#FF69B4',
                    fg='#333333' if temperature_var.get() != temp_value else 'white',
                    padx=8,
                    pady=2,
                    command=create_temp_preset_handler(temp_value, temp_label)
                )
                preset_btn.pack(side=tk.LEFT, padx=2)
                preset_btn.bind("<Enter>", 
                    lambda e, b=preset_btn: b.config(bg='#FFB6C1') if temperature_var.get() != temp_value else None)
                preset_btn.bind("<Leave>", 
                    lambda e, b=preset_btn, v=temp_value: 
                        b.config(bg='#FF69B4' if temperature_var.get() == v else '#FFF5F7'))
        
            # 当前值标签
            temperature_label_frame = tk.Frame(temperature_frame, bg='white')
            temperature_label_frame.pack(pady=(8, 0))
        
            temperature_label = tk.Label(
                temperature_label_frame,
                text=f"{temperature_var.get():.2f}",
                font=("Microsoft YaHei UI", 12, "bold"),
                bg='white',
                fg='#FF69B4'
            )
            temperature_label.pack(side=tk.LEFT)
        
            temp_description = tk.Label(
                temperature_label_frame,
                text="（适中，平衡）",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            )
            temp_description.pack(side=tk.LEFT, padx=(10, 0))
        
            # 初始化显示
            update_temperature_label(temperature_var.get())
        
            # Max Tokens调节
            max_tokens_frame = tk.Frame(config_area, bg='white')
            max_tokens_frame.pack(fill=tk.X, pady=(0, 20))
        
            tk.Label(
                max_tokens_frame,
                text="回复长度 (Max Tokens):",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333'
            ).pack(anchor=tk.W)
        
            # Max Tokens值显示和调节
            max_tokens_var = tk.IntVar(value=ai_config.get_max_tokens())
        
            def update_max_tokens_label(value):
                """更新max tokens标签显示"""
                tokens_value = int(float(value))
                max_tokens_label.config(text=f"{tokens_value}")
                # 根据值显示说明
                if tokens_value < 300:
                    description = "（简短回复）"
                elif tokens_value < 800:
                    description = "（适中长度）"
                elif tokens_value < 1500:
                    description = "（详细回复）"
                else:
                    description = "（非常详细）"
                tokens_description.config(text=description)
        
            # Max Tokens调节控件
            max_tokens_scale_frame = tk.Frame(max_tokens_frame, bg='white')
            max_tokens_scale_frame.pack(fill=tk.X, pady=(5, 0))
        
            # 最小值标签
            tk.Label(
                max_tokens_scale_frame,
                text="100",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            ).pack(side=tk.LEFT)
        
            # 滑动条
            max_tokens_scale = tk.Scale(
                max_tokens_scale_frame,
                from_=100,
                to=4000,
                resolution=100,
                variable=max_tokens_var,
                orient=tk.HORIZONTAL,
                length=280,
                showvalue=False,
                bg='white',
                fg='#333333',
                troughcolor='#FFF5F7',
                highlightthickness=0,
                sliderrelief=tk.FLAT,
                command=update_max_tokens_label
            )
            max_tokens_scale.pack(side=tk.LEFT, padx=10)
        
            # 最大值标签
            tk.Label(
                max_tokens_scale_frame,
                text="4000",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            ).pack(side=tk.LEFT)
        
            # Max Tokens预设按钮
            max_tokens_presets_frame = tk.Frame(max_tokens_frame, bg='white')
            max_tokens_presets_frame.pack(anchor=tk.W, pady=(5, 0))
        
            max_tokens_presets = [
                (100, "简短"),
                (300, "简洁"),
                (500, "适中"),
                (1000, "详细"),
                (2000, "非常详细"),
                (4000, "详尽")
            ]
        
            for tokens_value, tokens_label in max_tokens_presets:
                def create_tokens_preset_handler(val, label):
                    def handler():
                        max_tokens_var.set(val)
                        update_max_tokens_label(val)
                    return handler
            
                preset_btn = tk.Button(
                    max_tokens_presets_frame,
                    text=tokens_label,
                    font=("Microsoft YaHei UI", 8),
                    relief=tk.FLAT,
                    bg='#FFF5F7' if max_tokens_var.get() != tokens_value else '#FF69B4',
                    fg='#333333' if max_tokens_var.get() != tokens_value else 'white',
                    padx=8,
                    pady=2,
                    command=create_tokens_preset_handler(tokens_value, tokens_label)
                )
                preset_btn.pack(side=tk.LEFT, padx=2)
                preset_btn.bind("<Enter>", 
                    lambda e, b=preset_btn: b.config(bg='#FFB6C1') if max_tokens_var.get() != tokens_value else None)
                preset_btn.bind("<Leave>", 
                    lambda e, b=preset_btn, v=tokens_value: 
                        b.config(bg='#FF69B4' if max_tokens_var.get() == v else '#FFF5F7'))
        
            # 当前值标签
            max_tokens_label_frame = tk.Frame(max_tokens_frame, bg='white')
            max_tokens_label_frame.pack(pady=(8, 0))
        
            max_tokens_label = tk.Label(
                max_tokens_label_frame,
                text=f"{max_tokens_var.get()}",
                font=("Microsoft YaHei UI", 12, "bold"),
                bg='white',
                fg='#FF69B4'
            )
            max_tokens_label.pack(side=tk.LEFT)
        
            tokens_description = tk.Label(
                max_tokens_label_frame,
                text="（适中长度）",
                font=("Microsoft YaHei UI", 9),
                bg='white',
                fg='#666666'
            )
            tokens_description.pack(side=tk.LEFT, padx=(10, 0))
        
            # 初始化显示
            update_max_tokens_label(max_tokens_var.get())
        
            # 分隔线
            separator2 = tk.Frame(config_area, height=1, bg='#FFB6C1')
            separator2.pack(fill=tk.X, pady=(5, 15))
        
            # 截图分析配置部分
            screenshot_frame = tk.Frame(config_area, bg='white')
            screenshot_frame.pack(fill=tk.X, pady=(10, 0))
        
            # 截图分析复选框
            screenshot_var = tk.BooleanVar(
                value=ai_config.get_enable_screenshot_analysis()
            )
        
            def toggle_screenshot_checkbox():
                current = screenshot_var.get()
                screenshot_var.set(not current)
                update_screenshot_checkbox_display()
        
            def update_screenshot_checkbox_display():
                if screenshot_var.get():
                    screenshot_canvas.itemconfig(screenshot_bg, fill='#FF69B4')
                    screenshot_canvas.itemconfig(screenshot_check, text="✓")
                else:
                    screenshot_canvas.itemconfig(screenshot_bg, fill='white')
                    screenshot_canvas.itemconfig(screenshot_check, text="")
        
            # 截图分析复选框容器
            screenshot_check_frame = tk.Frame(screenshot_frame, bg='white')
            screenshot_check_frame.pack(anchor=tk.W, pady=(0, 10))
        
            # 复选框画布
            screenshot_canvas = tk.Canvas(
                screenshot_check_frame,
                width=20,
                height=20,
                bg='white',
                highlightthickness=0
            )
            screenshot_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
            # 复选框背景和边框
            screenshot_bg = screenshot_canvas.create_rectangle(
                2, 2, 18, 18,
                fill='white' if not screenshot_var.get() else '#FF69B4',
                outline='#FF69B4',
                width=2
            )
        
            # 复选框对勾
            screenshot_check = screenshot_canvas.create_text(
                10, 10,
                text="✓" if screenshot_var.get() else "",
                font=("Microsoft YaHei UI", 12, "bold"),
                fill='white'
            )
        
            screenshot_canvas.bind("<Button-1>", lambda e: toggle_screenshot_checkbox())
            screenshot_canvas.config(cursor='hand2')
        
            tk.Label(
                screenshot_check_frame,
                text="启用截图分析（定时分析屏幕内容）",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333',
                cursor='hand2'
            ).pack(side=tk.LEFT)
            screenshot_check_frame.bind("<Button-1>", lambda e: toggle_screenshot_checkbox())
        
            # 截图间隔设置
            interval_frame = tk.Frame(screenshot_frame, bg='white')
            interval_frame.pack(fill=tk.X, pady=(0, 10))
        
            tk.Label(
                interval_frame,
                text="截图间隔（秒）:",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333'
            ).pack(side=tk.LEFT)
        
            interval_var = tk.IntVar(value=ai_config.get_screenshot_interval())
            interval_spinbox = tk.Spinbox(
                interval_frame,
                from_=30,
                to=600,
                increment=30,
                textvariable=interval_var,
                width=8,
                font=("Microsoft YaHei UI", 10),
                relief=tk.FLAT,
                bg='#FFF5F7',
                highlightthickness=1,
                highlightcolor='#FFB6C1'
            )
            interval_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
            # 仅在空闲时分析复选框
            idle_only_var = tk.BooleanVar(
                value=ai_config.get_only_analyze_when_idle()
            )
        
            def toggle_idle_only_checkbox():
                current = idle_only_var.get()
                idle_only_var.set(not current)
                update_idle_only_checkbox_display()
        
            def update_idle_only_checkbox_display():
                if idle_only_var.get():
                    idle_only_canvas.itemconfig(idle_only_bg, fill='#FF69B4')
                    idle_only_canvas.itemconfig(idle_only_check, text="✓")
                else:
                    idle_only_canvas.itemconfig(idle_only_bg, fill='white')
                    idle_only_canvas.itemconfig(idle_only_check, text="")
        
            # 仅在空闲时分析复选框容器
            idle_only_frame = tk.Frame(screenshot_frame, bg='white')
            idle_only_frame.pack(anchor=tk.W, pady=(0, 20))
        
            # 复选框画布
            idle_only_canvas = tk.Canvas(
                idle_only_frame,
                width=20,
                height=20,
                bg='white',
                highlightthickness=0
            )
            idle_only_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
            # 复选框背景和边框
            idle_only_bg = idle_only_canvas.create_rectangle(
                2, 2, 18, 18,
                fill='white' if not idle_only_var.get() else '#FF69B4',
                outline='#FF69B4',
                width=2
            )
        
            # 复选框对勾
            idle_only_check = idle_only_canvas.create_text(
                10, 10,
                text="✓" if idle_only_var.get() else "",
                font=("Microsoft YaHei UI", 12, "bold"),
                fill='white'
            )
        
            idle_only_canvas.bind("<Button-1>", lambda e: toggle_idle_only_checkbox())
            idle_only_canvas.config(cursor='hand2')
        
            tk.Label(
                idle_only_frame,
                text="仅在宠物空闲时分析（节省资源）",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                fg='#333333',
                cursor='hand2'
            ).pack(side=tk.LEFT)
            idle_only_frame.bind("<Button-1>", lambda e: toggle_idle_only_checkbox())
        
            # 按钮区域
            button_frame = tk.Frame(config_area, bg='white')
            button_frame.pack(fill=tk.X, pady=(20, 0))

            # 保存按钮（粉色样式）
            def create_pink_button(parent, text, command):
                btn_frame = tk.Frame(parent, bg='white')
                btn_frame.pack(side=tk.LEFT, padx=5, expand=True)
        
                canvas = tk.Canvas(
                    btn_frame,
                    width=80,
                    height=32,
                    bg='white',
                    highlightthickness=0
                )
                canvas.pack()
        
                # 按钮背景
                btn_bg = canvas.create_rectangle(
                    2, 2, 78, 30,
                    fill='#FF69B4',
                    outline='#FF1493',
                    width=2
                )
        
                # 按钮文字
                btn_text = canvas.create_text(
                    40, 16,
                    text=text,
                    font=("Microsoft YaHei UI", 10, "bold"),
                    fill='white'
                )
        
                # 事件绑定
                def on_btn_enter(e):
                    canvas.itemconfig(btn_bg, fill='#FF1493')
                    canvas.config(cursor='hand2')
        
                def on_btn_leave(e):
                    canvas.itemconfig(btn_bg, fill='#FF69B4')
                    canvas.config(cursor='')
        
                canvas.bind("<Enter>", on_btn_enter)
                canvas.bind("<Leave>", on_btn_leave)
                canvas.bind("<Button-1>", lambda e: command())
        
                return canvas
    
            # 保存配置函数
            def save_ai_config():
                api_key = api_key_var.get().strip()
                ai_enabled = ai_enabled_var.get()
        
                # AI参数
                temperature = temperature_var.get()
                max_tokens = max_tokens_var.get()
        
                # 截图分析配置
                enable_screenshot = screenshot_var.get()
                screenshot_interval = interval_var.get()
                only_when_idle = idle_only_var.get()
        
                # 保存到AI配置文件
                ai_config.config["api_key"] = api_key
                ai_config.config["enable_ai"] = ai_enabled
                ai_config.config["temperature"] = temperature
                ai_config.config["max_tokens"] = max_tokens
                ai_config.config["enable_screenshot_analysis"] = enable_screenshot
                ai_config.config["screenshot_interval"] = screenshot_interval
                ai_config.config["only_analyze_when_idle"] = only_when_idle
                ai_config.save_config()
        
                # 保存到主配置文件
                config["api_key"] = api_key
                config["ai_enabled"] = ai_enabled
                save_config(config)
        
                # 重新初始化AI处理器
                app.init_ai_handler(config)
        
                # 重启截图分析定时器
                if hasattr(app, 'start_screenshot_analysis'):
                    app.start_screenshot_analysis()
        
                config_window.destroy()
        
                # 显示成功消息
                success_window = tk.Toplevel(app.root)
                success_window.title("提示")
                success_window.geometry("300x150")
                success_window.attributes("-topmost", True)
                success_window.configure(bg='#FFB6C1')
        
                # 居中
                success_window.update_idletasks()
                screen_w = success_window.winfo_screenwidth()
                screen_h = success_window.winfo_screenheight()
                x = (screen_w - 300) // 2
                y = (screen_h - 150) // 2
                success_window.geometry(f"+{x}+{y}")
        
                content_frame = tk.Frame(success_window, bg='white')
                content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
                tk.Label(
                    content_frame,
                    text="✓ 配置已保存！",
                    font=("Microsoft YaHei UI", 12),
                    fg='#FF69B4',
                    bg='white',
                    pady=20
                ).pack()
        
                tk.Label(
                    content_frame,
                    text="右键点击宠物可打开聊天窗口",
                    font=("Microsoft YaHei UI", 10),
                    bg='white',
                    pady=10
                ).pack()
        
                # 圆形确认按钮
                ok_btn_frame = tk.Frame(content_frame, bg='white')
                ok_btn_frame.pack(pady=10)
        
                ok_canvas = tk.Canvas(
                    ok_btn_frame,
                    width=60,
                    height=30,
                    bg='white',
                    highlightthickness=0
                )
                ok_canvas.pack()
        
                ok_bg = ok_canvas.create_rectangle(
                    2, 2, 58, 28,
                    fill='#FF69B4',
                    outline='#FF1493',
                    width=2
                )
                ok_text = ok_canvas.create_text(
                    30, 15,
                    text="确定",
                    font=("Microsoft YaHei UI", 10, "bold"),
                    fill='white'
                )
        
                def on_ok_enter(e):
                    ok_canvas.itemconfig(ok_bg, fill='#FF1493')
                    ok_canvas.config(cursor='hand2')
        
                def on_ok_leave(e):
                    ok_canvas.itemconfig(ok_bg, fill='#FF69B4')
                    ok_canvas.config(cursor='')
        
                ok_canvas.bind("<Enter>", on_ok_enter)
                ok_canvas.bind("<Leave>", on_ok_leave)
                ok_canvas.bind("<Button-1>", lambda e: success_window.destroy())
        
                # 3秒后自动关闭
                success_window.after(3000, success_window.destroy)

            # 取消按钮
            def close_window():
                config_window.destroy()
    
            # 创建按钮
            save_button = create_pink_button(button_frame, "保存配置", save_ai_config)
            cancel_button = create_pink_button(button_frame, "取消", close_window)
        
            # 调整窗口到顶部
            config_window.update_idletasks()
            canvas.yview_moveto(0)

        except ImportError as e:
            print(f"导入AI配置模块失败: {e}")
        
            # 显示错误窗口（粉色样式）
            error_window = tk.Toplevel(app.root)
            error_window.title("错误")
            error_window.geometry("300x150")
            error_window.attributes("-topmost", True)
            error_window.configure(bg='#FFB6C1')
        
            content_frame = tk.Frame(error_window, bg='white')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
            tk.Label(
                content_frame,
                text="AI模块加载失败",
                font=("Microsoft YaHei UI", 12),
                fg='#FF4444',
                bg='white',
                pady=20
            ).pack()
        
            tk.Label(
                content_frame,
                text="请检查ai_handler.py是否存在",
                font=("Microsoft YaHei UI", 10),
                bg='white',
                pady=10
            ).pack()
        
            # 圆形确定按钮
            ok_frame = tk.Frame(content_frame, bg='white')
            ok_frame.pack(pady=10)
        
            ok_canvas = tk.Canvas(
                ok_frame,
                width=60,
                height=30,
                bg='white',
                highlightthickness=0
            )
            ok_canvas.pack()
        
            ok_bg = ok_canvas.create_rectangle(
                2, 2, 58, 28,
                fill='#FF69B4',
                outline='#FF1493',
                width=2
            )
            ok_text = ok_canvas.create_text(
                30, 15,
                text="确定",
                font=("Microsoft YaHei UI", 10, "bold"),
                fill='white'
            )
        
            def on_ok_enter(e):
                ok_canvas.itemconfig(ok_bg, fill='#FF1493')
                ok_canvas.config(cursor='hand2')
        
            def on_ok_leave(e):
                ok_canvas.itemconfig(ok_bg, fill='#FF69B4')
                ok_canvas.config(cursor='')
        
            ok_canvas.bind("<Enter>", on_ok_enter)
            ok_canvas.bind("<Leave>", on_ok_leave)
            ok_canvas.bind("<Button-1>", lambda e: error_window.destroy())






    def on_about(icon, item):
        """显示关于信息"""
        about_window = tk.Toplevel(app.root)
        about_window.title("桌面宠物 - AI版")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.attributes("-topmost", True)

        # 居中显示
        about_window.update_idletasks()
        screen_w = about_window.winfo_screenwidth()
        screen_h = about_window.winfo_screenheight()
        x = (screen_w - 500) // 2
        y = (screen_h - 400) // 2
        about_window.geometry(f"+{x}+{y}")

        # 主内容 Frame
        content_frame = tk.Frame(about_window, padx=30, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(
            content_frame,
            text="桌面宠物 AI版",
            font=("Microsoft YaHei UI", 20, "bold"),
        ).pack(pady=(0, 20))

        # 功能介绍
        features = [
            "• 可爱的桌面宠物，可在屏幕上自由移动",
            "• 支持跟随鼠标功能",
            "• 支持鼠标穿透，不影响正常操作",
            "• 右键点击宠物打开聊天窗口",
            "• 集成DeepSeek AI聊天功能",
            "• 可调节AI回复随机性和长度",
            "• 智能截图分析，主动发起话题",
            "• 可自定义宠物大小和透明度",
            "• 系统托盘控制，方便操作"
        ]
        
        for feature in features:
            tk.Label(
                content_frame,
                text=feature,
                font=("Microsoft YaHei UI", 10),
                justify=tk.LEFT,
                anchor=tk.W
            ).pack(anchor=tk.W, pady=2)

        # 使用说明
        tk.Label(
            content_frame,
            text="\n使用说明：",
            font=("Microsoft YaHei UI", 11, "bold"),
            anchor=tk.W
        ).pack(anchor=tk.W, pady=(10, 5))

        instructions = [
            "1. 右键托盘图标配置AI API密钥",
            "2. 右键点击宠物打开聊天窗口",
            "3. 在输入框中输入消息与AI对话",
            "4. 左键拖动可移动宠物位置",
            "5. 可在AI配置中调节回复随机性和长度"
        ]
        
        for instruction in instructions:
            tk.Label(
                content_frame,
                text=instruction,
                font=("Microsoft YaHei UI", 9),
                justify=tk.LEFT,
                anchor=tk.W
            ).pack(anchor=tk.W, pady=1)

        # 关闭按钮
        tk.Button(
            content_frame,
            text="确定",
            command=about_window.destroy,
            width=12,
            font=("Microsoft YaHei UI", 10),
        ).pack(pady=(20, 0))

    # 创建缩放菜单项
    def create_scale_items():
        from pet_window import SCALE_OPTIONS
        
        scale_items = []
        for i in range(len(SCALE_OPTIONS)):
            def make_scale_handler(idx):
                def handler(icon, item):
                    app.set_scale(idx)
                return handler
            
            scale_items.append(
                pystray.MenuItem(
                    f"{SCALE_OPTIONS[i]}x",
                    make_scale_handler(i),
                    checked=lambda item, idx=i: app.scale_index == idx,
                    radio=True,
                )
            )
        return pystray.Menu(*scale_items)

    # 创建透明度菜单项
    def create_transparency_items():
        from pet_window import TRANSPARENCY_OPTIONS
        
        transparency_items = []
        for i in range(len(TRANSPARENCY_OPTIONS)):
            def make_transparency_handler(idx):
                def handler(icon, item):
                    app.set_transparency(idx)
                return handler
            
            transparency_items.append(
                pystray.MenuItem(
                    f"{int(TRANSPARENCY_OPTIONS[i] * 100)}%",
                    make_transparency_handler(i),
                    checked=lambda item, idx=i: app.transparency_index == idx,
                    radio=True,
                )
            )
        return pystray.Menu(*transparency_items)

    # 创建菜单
    menu = pystray.Menu(
        pystray.MenuItem(
            "隐藏/显示",
            on_toggle_visible,
        ),
        pystray.MenuItem(
            "暂停/继续",
            on_toggle_pause,
        ),
        pystray.MenuItem(
            "打开聊天",
            on_toggle_chat,
        ),
        pystray.MenuItem(
            "截图分析",
            on_toggle_screenshot_analysis,
            checked=lambda item: app.enable_screenshot_analysis if hasattr(app, 'enable_screenshot_analysis') else False,
        ),
        pystray.MenuItem(
            "跟随鼠标",
            on_toggle_follow,
            checked=lambda item: app.follow_mouse,
        ),
        pystray.MenuItem(
            "鼠标穿透",
            on_toggle_click_through,
            checked=lambda item: app.click_through,
        ),
        pystray.MenuItem("AI配置", on_configure_ai),
        pystray.MenuItem("缩放", create_scale_items()),
        pystray.MenuItem("透明度", create_transparency_items()),
        pystray.MenuItem("关于", on_about),
        pystray.MenuItem("退出", on_quit),
    )

    # 创建托盘图标
    icon = pystray.Icon("desktop_pet", icon_image, "桌面宠物 AI版", menu)
    app.app = icon
    
    return icon