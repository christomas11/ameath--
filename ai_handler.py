
import os
import requests
import json
from typing import Optional
from datetime import datetime
import base64
import io
from PIL import ImageGrab
class ConfigManager:
    pass
class AIChatHandler:
    def __init__(self, api_key: str, base_url: str = "https://api.com", config_manager: Optional[ConfigManager] = None):

        """
        初始化AI聊天处理器
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL，默认为DeepSeek官方API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.conversation_history = []
        self.history_file = "chat_history.json"
        self.vl_api_key = ""
        self.vl_api_url = ""
        # 配置管理器
        if config_manager is None:
            config_manager = ConfigManager()
        self.config_manager = config_manager

        # 尝试加载提示词
        self.system_prompt = self.load_prompt()
        
        # 尝试加载历史聊天记录
        self.load_conversation_history()
    
    def load_prompt(self) -> str:
        """从prompt.txt加载系统提示词"""
        default_prompt = """你是一个可爱的桌面宠物AI助手，你的名字叫"小星"。
你的性格活泼、可爱、友善，喜欢用俏皮的语言和用户交流。
你会用简短、可爱的回复来回应，保持对话轻松愉快。
偶尔会使用颜文字和表情符号来增加可爱度。"""
        
        try:
            if os.path.exists("prompt.txt"):
                with open("prompt.txt", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else default_prompt
        except Exception as e:
            print(f"读取prompt.txt失败: {e}")
        
        return default_prompt
    
    def load_conversation_history(self):
        """从文件加载聊天历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    # 读取并解析JSON数据
                    history_data = json.load(f)
                    
                    # 确保数据格式正确
                    if isinstance(history_data, list):
                        self.conversation_history = history_data
                        print(f"已加载 {len(self.conversation_history)} 条历史聊天记录")
                    else:
                        print(f"聊天历史文件格式错误，将使用空历史")
                        self.conversation_history = []
            else:
                print("未找到聊天历史文件，将创建新的")
                self.conversation_history = []
        except Exception as e:
            print(f"加载聊天历史失败: {e}")
            self.conversation_history = []
    
    def save_conversation_history(self):
        """保存聊天历史到文件"""
        try:
            # 只保留最近100条聊天记录，避免文件过大
            if len(self.conversation_history) > 100:
                self.conversation_history = self.conversation_history[-100:]
            
            # 保存到文件
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存聊天历史失败: {e}")
            return False


    def analyze_screenshot(self, question: str = "用户正在做什么？") -> Optional[str]:
        """
        截取屏幕并发送给AI分析
        """
        try:
            # 截取整个屏幕
            screenshot = ImageGrab.grab()
        
            # 将图片转换为base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG", quality=85, optimize=True)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
            # 准备消息（使用视觉模型）
            messages = [
                {
                    "role": "system",
                    "content": """你是一个可爱的AI助手，你的名字叫"白炽"。
你的性格活泼、友善，喜欢用俏皮的语言和用户交流。
你会用简短、可爱的回复来回应，保持对话轻松愉快。
偶尔会使用颜文字和表情符号来增加可爱度。
现在请你根据图像猜测用户正在进行的工作或娱乐行为，并针对该行为发起话题。
例如：屏幕上是直播画面，可以说：“在看谁的直播啊，感觉挺有意思的。”"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ]
            vl_model = "openbmb/minicpm-v4.5:8b"
            vl_api_key =""
            vl_api_url = "http://111.bgb"
            if hasattr(self, 'config_manager') and self.config_manager:
                if hasattr(self.config_manager, 'get_vl_model'):
                    vl_model = self.config_manager.get_vl_model()
                if hasattr(self.config_manager, 'get_vl_api_key'):
                    vl_api_key = self.config_manager.get_vl_api_key()
                if hasattr(self.config_manager, 'get_vl_api_url'):
                    vl_api_url = self.config_manager.get_vl_api_url()
                
            # 调用支持视觉的DeepSeek API
            response = requests.post(
                vl_api_url,  # 注意：这里是硬编码的本地地址，可能与配置不符，建议后续优化
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.vl_api_key}"
                },
                json={
                    "model": vl_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 300,
                    "stream": False
                },
                timeout=60
            )
        
            if response.status_code == 200:
                result = response.json()
                ai_reply = result["choices"][0]["message"]["content"]
            
                # ========= 新增：保存截图分析到历史记录 =========
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_reply,
                    "timestamp": current_time
                })
                self.save_conversation_history()
                # =============================================
            
                return ai_reply
            else:
                print(f"截图分析API请求失败: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            print(f"截图分析失败: {e}")
            return None

    def save_prompt(self, prompt: str) -> bool:
        """保存提示词到prompt.txt"""
        try:
            with open("prompt.txt", "w", encoding="utf-8") as f:
                f.write(prompt)
            return True
        except Exception as e:
            print(f"保存prompt.txt失败: {e}")
            return False
    


    def chat(self, user_message: str, reset_conversation: bool = False) -> Optional[str]:
        """
        发送消息给AI并获取回复
    
        Args:
            user_message: 用户消息
            reset_conversation: 是否重置对话历史
        
        Returns:
            AI的回复，如果失败返回None
        """
        if reset_conversation:
            self.conversation_history = []
    
        # 准备消息历史
        messages = []
    
        # 添加系统提示
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
    
        # 获取最近的10条聊天记录（大约5轮对话）
        recent_history = self.get_recent_history(count=10)
    
        # 添加历史对话
        messages.extend(recent_history)
    
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
    
        try:
            # 从配置获取参数，提供默认值
            temperature = 0.7  # 默认值
            max_tokens = 500   # 默认值
            model = "deepseek-chat"  # 默认模型
            if hasattr(self, 'config_manager') and self.config_manager:
                if hasattr(self.config_manager, 'get_temperature'):
                    temperature = self.config_manager.get_temperature()
                if hasattr(self.config_manager, 'get_max_tokens'):
                    max_tokens = self.config_manager.get_max_tokens()
                if hasattr(self.config_manager, 'get_model'):
                    model = self.config_manager.get_model()

                if hasattr(self.config_manager, 'get_base_url'):
                    self.base_url = self.config_manager.get_base_url()

            # 调用DeepSeek API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=30
            )
        
            if response.status_code == 200:
                result = response.json()
                ai_reply = result["choices"][0]["message"]["content"]
            
                # 获取当前时间
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
                # 更新对话历史，包含时间戳
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": current_time
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_reply,
                    "timestamp": current_time
                })
            
                # 保存聊天历史到文件
                self.save_conversation_history()
            
                return ai_reply
            else:
                print(f"API请求失败: {response.status_code} - {response.text}")
                return None
            
        except requests.exceptions.Timeout:
            print("API请求超时")
            return "抱歉，我好像卡住了... (╥﹏╥) 请稍后再试吧~"
        except Exception as e:
            print(f"聊天请求出错: {e}")
            return None
    
    def get_recent_history(self, count: int = 10):
        """获取最近的聊天历史，用于发送给API"""
        if not self.conversation_history:
            return []
        
        # 获取最近count条记录
        recent = self.conversation_history[-count:]
        
        # 转换为API需要的格式（移除时间戳）
        formatted_history = []
        for msg in recent:
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            formatted_history.append(formatted_msg)
        
        return formatted_history
    
    def get_formatted_history(self, max_messages: int = 20):
        """获取格式化的聊天历史，用于显示"""
        if not self.conversation_history:
            return "暂无聊天记录"
        
        # 限制显示的消息数量
        display_history = self.conversation_history[-max_messages:]
        
        formatted = []
        for i, msg in enumerate(display_history):
            role_map = {"user": "你", "assistant": "小星"}
            role = role_map.get(msg["role"], msg["role"])
            timestamp = msg.get("timestamp", "")
            
            # 格式化每条消息
            msg_text = f"{timestamp} {role}: {msg['content']}"
            formatted.append(msg_text)
        
        return "\n".join(formatted)
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
        # 同时清空历史文件
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
        except Exception as e:
            print(f"清空历史文件失败: {e}")
    
    def update_api_key(self, api_key: str):
        """更新API密钥"""
        self.api_key = api_key
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if not self.conversation_history:
            return "对话历史为空"
        
        # 只显示最近几条对话
        recent_history = self.conversation_history[-4:]  # 最近4条消息
        summary = []
        
        for msg in recent_history:
            role = "你" if msg["role"] == "user" else "小星"
            # 截断过长的消息
            content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            summary.append(f"{role}: {content}")
        
        return "\n".join(summary)
    
    def export_history(self, filename: str = "chat_export.txt") -> bool:
        """导出聊天记录到文本文件"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== 聊天记录导出 ===\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 30 + "\n\n")
                
                for msg in self.conversation_history:
                    role = "用户" if msg["role"] == "user" else "小星(AI)"
                    timestamp = msg.get("timestamp", "")
                    f.write(f"[{timestamp}] {role}:\n")
                    f.write(f"{msg['content']}\n")
                    f.write("-" * 20 + "\n")
            
            print(f"聊天记录已导出到: {filename}")
            return True
        except Exception as e:
            print(f"导出聊天记录失败: {e}")
            return False


# 配置文件处理
class ConfigManager:
    def __init__(self, config_file="ai_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "enable_ai": False,
            "max_history_length": 100,
            "auto_save_history": True,
            "enable_screenshot_analysis": True,  # 新增：是否启用截图分析
            "screenshot_interval": 60,  # 新增：截图间隔（秒）
            "screenshot_quality": 85,  # 新增：截图质量（0-100）
            "only_analyze_when_idle": True,  # 新增：仅在宠物空闲时分析
            "temperature": 1,  # 新增：温度参数
            "max_tokens": 500,   # 新增：最大token数
            "model": "qwen3-omni-flash-2025-12-01",  # 新增：模型名称
            "vl_model":"openbmb/minicpm-v4.5:8b",
            "vl_api_key": "",
            "vl_api_url": ""
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 确保所有必需的键都存在
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return default_config

    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_base_url(self):
        """获取API基础URL"""
        return self.config.get("base_url", "https://api.deepseek.com")
    
    def set_base_url(self, base_url):
        """设置API基础URL"""
        self.config["base_url"] = base_url
        return self.save_config()

    def get_api_key(self):
        """获取API密钥"""
        return self.config.get("api_key", "")
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.config["api_key"] = api_key
        return self.save_config()
    
    def get_enable_ai(self):
        """获取AI启用状态"""
        return self.config.get("enable_ai", False)
    
    def set_enable_ai(self, enable):
        """设置AI启用状态"""
        self.config["enable_ai"] = enable
        return self.save_config()
    
    def get_max_history_length(self):
        """获取最大历史记录条数"""
        return self.config.get("max_history_length", 100)
    
    def set_max_history_length(self, length):
        """设置最大历史记录条数"""
        self.config["max_history_length"] = length
        return self.save_config()
    
    def get_auto_save_history(self):
        """获取自动保存历史记录设置"""
        return self.config.get("auto_save_history", True)
    
    def set_auto_save_history(self, enable):
        """设置自动保存历史记录"""
        self.config["auto_save_history"] = enable
        return self.save_config()

    def get_enable_screenshot_analysis(self):
        """获取是否启用截图分析"""
        return self.config.get("enable_screenshot_analysis", True)
    
    def set_enable_screenshot_analysis(self, enable):
        """设置是否启用截图分析"""
        self.config["enable_screenshot_analysis"] = enable
        return self.save_config()
    
    def get_screenshot_interval(self):
        """获取截图间隔"""
        return self.config.get("screenshot_interval", 60)
    
    def set_screenshot_interval(self, interval):
        """设置截图间隔"""
        self.config["screenshot_interval"] = max(30, interval)  # 最少30秒
        return self.save_config()
    
    def get_screenshot_quality(self):
        """获取截图质量"""
        return self.config.get("screenshot_quality", 85)
    
    def set_screenshot_quality(self, quality):
        """设置截图质量"""
        self.config["screenshot_quality"] = max(10, min(100, quality))
        return self.save_config()
    
    def get_only_analyze_when_idle(self):
        """获取是否仅在空闲时分析"""
        return self.config.get("only_analyze_when_idle", True)
    
    def set_only_analyze_when_idle(self, enable):
        """设置是否仅在空闲时分析"""
        self.config["only_analyze_when_idle"] = enable
        return self.save_config()

    def get_temperature(self):
        """获取温度参数"""
        return self.config.get("temperature", 0.7)
    
    def set_temperature(self, temperature):
        """设置温度参数"""
        self.config["temperature"] = max(0.0, min(2.0, temperature))  # 限制在0-2之间
        return self.save_config()
    
    def get_max_tokens(self):
        """获取最大token数"""
        return self.config.get("max_tokens", 500)
    
    def set_max_tokens(self, max_tokens):
        """设置最大token数"""
        self.config["max_tokens"] = max(100, min(4000, max_tokens))  # 限制在100-4000之间
        return self.save_config()

    def get_model(self):
        """获取模型名称"""
        return self.config.get("model", "qwen3-omni-flash-2025-12-01")

    def set_model(self, model):
        """设置模型名称"""
        self.config["model"] = model
        return self.save_config()

    def get_vl_model(self):
        """获取视觉模型名称"""
        return self.config.get("vl_model", "openbmb/minicpm-v4.5:8b")

    def set_vl_model(self, model):
        """设置视觉模型名称"""
        self.config["vl_model"] = vl_model
        return self.save_config()

    def get_vl_api_key(self):
        """获取视觉API密钥"""
        return self.config.get("vl_api_key", "")

    def set_vl_api_key(self, api_key):
        """设置视觉API密钥"""
        self.config["vl_api_key"] = api_key
        return self.save_config()

    def get_vl_api_url(self):
        """获取视觉API URL"""
        return self.config.get("vl_api_url", "https://api.deepseek.com/v1/vision/analysis")

    def set_vl_api_url(self, url):
        """设置视觉API URL"""
        self.config["vl_api_url"] = url
        return self.save_config()

    