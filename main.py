import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import time
import threading
from pynput import keyboard

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("鼠标连点器")
        self.root.geometry("350x280")
        self.root.resizable(False, False)

        # 状态变量
        self.is_clicking = False
        self.target_position = None
        self.running = True

        # 界面布局
        self.create_widgets()

        # 启动点击线程
        self.click_thread = threading.Thread(target=self.clicker_loop, daemon=True)
        self.click_thread.start()

        # 启动监听线程
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+,': self.toggle_clicking,
            '<ctrl>+.': self.quit_app
        })
        self.listener.start()

        # 处理窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def create_widgets(self):
        # 样式设置
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=5)

        # 1. 坐标显示区域
        frame_pos = ttk.LabelFrame(self.root, text=" 目标位置 ", padding=10)
        frame_pos.pack(fill="x", padx=10, pady=5)

        self.lbl_position = ttk.Label(frame_pos, text="当前未设置目标位置")
        self.lbl_position.pack(side="left")

        self.btn_set_pos = ttk.Button(frame_pos, text="选择位置", command=self.start_selection)
        self.btn_set_pos.pack(side="right")

        # 2. 参数设置区域
        frame_settings = ttk.LabelFrame(self.root, text=" 设置 ", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_settings, text="点击间隔(秒):").pack(side="left")
        
        self.var_interval = tk.DoubleVar(value=0.01)
        # Spinbox increment handling can be tricky, let's keep it simple
        spin_interval = ttk.Spinbox(frame_settings, from_=0.001, to=10.0, increment=0.01, 
                                    textvariable=self.var_interval, width=10)
        spin_interval.pack(side="left", padx=5)

        # 3. 控制按钮区域
        frame_ctrl = ttk.Frame(self.root, padding=10)
        frame_ctrl.pack(fill="x", padx=10)

        self.btn_start = ttk.Button(frame_ctrl, text="开始点击 (Ctrl+,)", command=self.toggle_clicking)
        self.btn_start.pack(fill="x", pady=2)

        # 4. 说明区域
        lbl_help = ttk.Label(self.root, text="快捷键: [Ctrl+,] 开始/暂停  [Ctrl+.] 退出程序", 
                             foreground="gray", font=("Arial", 9))
        lbl_help.pack(side="bottom", pady=5)
        
        # 5. 状态栏
        self.lbl_status = ttk.Label(self.root, text="就绪", relief="sunken", anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

    def start_selection(self):
        """开始选择位置"""
        self.btn_set_pos.config(state="disabled")
        
        # 创建全屏透明窗口
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-alpha', 0.3)
        self.overlay.configure(bg='black')
        self.overlay.config(cursor="crosshair")

        # 创建画布绘制十字线
        self.canvas = tk.Canvas(self.overlay, bg='black', highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        # 初始十字线
        screen_w = self.overlay.winfo_screenwidth()
        screen_h = self.overlay.winfo_screenheight()
        self.h_line = self.canvas.create_line(0, 0, screen_w, 0, fill="red", width=2)
        self.v_line = self.canvas.create_line(0, 0, 0, screen_h, fill="red", width=2)

        # 绑定事件
        self.canvas.bind('<Motion>', self.update_crosshair)
        self.canvas.bind('<Button-1>', self.confirm_selection)
        self.canvas.bind('<Button-3>', self.cancel_selection)
        self.canvas.bind('<Escape>', lambda e: self.cancel_selection(e))
        self.overlay.bind('<Escape>', lambda e: self.cancel_selection(e))
        
        # 确保窗口获得焦点，以便接收按键事件
        self.overlay.focus_set()

    def update_crosshair(self, event):
        """更新十字线位置"""
        x, y = event.x, event.y
        screen_w = self.overlay.winfo_screenwidth()
        screen_h = self.overlay.winfo_screenheight()
        self.canvas.coords(self.h_line, 0, y, screen_w, y)
        self.canvas.coords(self.v_line, x, 0, x, screen_h)

    def confirm_selection(self, event):
        """确认选择位置"""
        x = event.x_root
        y = event.y_root
        self.target_position = (x, y)
        self.lbl_position.config(text=f"X: {x}, Y: {y}")
        self.update_status(f"位置已锁定: ({x}, {y})")
        self.close_selection()
        
        # 选定位置后自动开始
        if not self.is_clicking:
            self.toggle_clicking()

    def cancel_selection(self, event=None):
        """取消选择"""
        self.update_status("取消选择")
        self.close_selection()

    def close_selection(self):
        """关闭选择窗口"""
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.btn_set_pos.config(state="normal")

    def toggle_clicking(self):
        """切换点击状态"""
        if not self.target_position:
            # 只有通过按钮调用时才弹窗，如果是快捷键调用，最好只在状态栏提示，避免阻塞
            # 这里简单起见都检查
            # 为了防止快捷键触发时弹窗阻塞线程，我们可以只在GUI线程做检查
            # 实际上 pynput 回调是在新线程，调用 tkinter 方法需要 careful
            pass

        # 切换逻辑有点复杂，因为 pynput 是在非主线程调用的
        # 我们使用 after_idle 或者 after 0 来在主线程执行
        self.root.after(0, self._toggle_clicking_main_thread)

    def _toggle_clicking_main_thread(self):
        if not self.target_position:
            self.update_status("错误: 请先设置目标位置！")
            messagebox.showwarning("提示", "请先设置目标位置！")
            return

        self.is_clicking = not self.is_clicking
        
        if self.is_clicking:
            self.btn_start.config(text="暂停点击 (Ctrl+,)")
            self.update_status("正在运行...")
        else:
            self.btn_start.config(text="开始点击 (Ctrl+,)")
            self.update_status("已暂停")

    def clicker_loop(self):
        """后台点击循环"""
        while self.running:
            if self.is_clicking and self.target_position:
                try:
                    # 使用 getattr 兼容不同版本的 pyautogui 此时返回的对象
                    x = getattr(self.target_position, 'x', self.target_position[0])
                    y = getattr(self.target_position, 'y', self.target_position[1])
                    pyautogui.click(x=x, y=y)
                    
                    sleep_time = 0.01
                    try:
                        sleep_time = float(self.var_interval.get())
                    except:
                        pass
                    if sleep_time < 0.001: sleep_time = 0.001
                    
                    time.sleep(sleep_time)
                except Exception as e:
                    print(f"点击出错: {e}")
                    # 出错则停止
                    self.is_clicking = False
                    self.root.after(0, lambda: self.btn_start.config(text="开始点击 (Ctrl+,)"))
            else:
                time.sleep(0.1)

    def update_status(self, text):
        self.lbl_status.config(text=text)

    def quit_app(self):
        """退出程序"""
        self.running = False
        self.is_clicking = False
        # 停止监听需要在非主线程调用 stop 吗？
        # pynput listener stop 可以在任何地方调用
        self.listener.stop()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    # 禁用 pyautogui 的自动防故障功能
    pyautogui.FAILSAFE = False
    
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
