import tkinter as tk
from tkinter import ttk
import time


class EditableLabel(tk.Entry):
    def __init__(self, parent, text, font, **kwargs):
        super().__init__(parent, font=font, bd=0, relief="flat", **kwargs)
        self.default_text = text
        self.insert(0, text)
        self.config(state="readonly", readonlybackground=self["background"])
        self.bind("<Button-1>", self.make_editable)
        self.bind("<FocusOut>", self.make_readonly)
        self.bind("<Return>", self.make_readonly)
        
        # 添加鼠标悬停效果
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda e: self.config(cursor=""))

    def make_editable(self, event=None):
        self.config(state="normal")
        self.focus()
        self.select_range(0, tk.END)

    def make_readonly(self, event=None):
        self.default_text = self.get()
        self.config(state="readonly")


class Stopwatch:
    def __init__(self, master, on_remove):
        self.master = master
        self.on_remove = on_remove
        self.running = False
        self.start_time = None
        self.elapsed = 0

        # 使用更现代的样式
        self.frame = ttk.Frame(master)
        self.frame.pack_configure(fill="x", padx=15, pady=8)
        self.frame.update_idletasks()  # 立即更新frame布局
        
        # 创建内部框架并添加圆角和阴影效果
        self.inner_frame = tk.Frame(self.frame, bg="#f0f0f0", relief="flat")
        self.inner_frame.pack_configure(fill="x", padx=2, pady=2)
        self.inner_frame.update_idletasks()  # 立即更新inner_frame布局

        # 更紧凑和现代的布局
        self.title_entry = EditableLabel(
            self.inner_frame,
            text="秒表",
            font=("Helvetica", 12),
            width=8,
            bg="#f0f0f0"
        )
        self.title_entry.grid(row=0, column=0, padx=(8, 5), pady=6, sticky="w")

        self.time_label = ttk.Label(
            self.inner_frame,
            text="00:00:00.0",
            font=("Helvetica", 12),
            style="Timer.TLabel"
        )
        self.time_label.grid(row=0, column=1, padx=(5, 10), pady=6, sticky="w")

        # 按钮样式
        button_frame = ttk.Frame(self.inner_frame)
        button_frame.grid(row=0, column=2, padx=(0, 8), pady=6, sticky="e")

        self.toggle_button = ttk.Button(
            button_frame,
            text="开始",
            width=5,
            command=self.toggle,
            style="Action.TButton"
        )
        self.toggle_button.pack(side="left", padx=2)

        self.reset_button = ttk.Button(
            button_frame,
            text="重置",
            width=5,
            command=self.reset,
            style="Secondary.TButton"
        )
        self.reset_button.pack(side="left", padx=2)

        self.remove_button = ttk.Button(
            button_frame,
            text="删除",
            width=5,
            command=self.remove,
            style="Danger.TButton"
        )
        self.remove_button.pack(side="left", padx=2)

        self.inner_frame.columnconfigure(1, weight=1)
        
        # 强制更新所有子组件的布局
        button_frame.update_idletasks()
        self.inner_frame.update_idletasks()
        self.frame.update_idletasks()
        
        self.update_loop()

    def toggle(self):
        if not self.running:
            self.start()
        else:
            self.stop()

    def start(self):
        self.running = True
        self.start_time = time.time() - self.elapsed
        self.toggle_button.config(text="停止")
        self.inner_frame.configure(bg="#e8f5e9")  # 运行时的背景色
        self.title_entry.configure(bg="#e8f5e9")

    def stop(self):
        self.running = False
        self.elapsed = time.time() - self.start_time
        self.toggle_button.config(text="开始")
        self.inner_frame.configure(bg="#f0f0f0")  # 恢复默认背景色
        self.title_entry.configure(bg="#f0f0f0")

    def reset(self):
        self.running = False
        self.elapsed = 0
        self.start_time = None
        self.toggle_button.config(text="开始")
        self.update_label()
        self.inner_frame.configure(bg="#f0f0f0")
        self.title_entry.configure(bg="#f0f0f0")

    def remove(self):
        self.running = False
        self.frame.destroy()
        self.on_remove(self)

    def update_loop(self):
        if self.running:
            self.elapsed = time.time() - self.start_time
            self.update_label()
        self.frame.after(100, self.update_loop)

    def update_label(self):
        total_ms = int(self.elapsed * 10)
        hours = total_ms // 36000
        minutes = (total_ms // 600) % 60
        seconds = (total_ms // 10) % 60
        tenths = total_ms % 10
        self.time_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}.{tenths}")


class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多功能秒表")
        self.root.geometry("450x200")  # 减小窗口初始宽度
        self.root.configure(bg="#ffffff")
        self.root.attributes("-topmost", True)
        
        # 设置最小窗口大小
        self.root.minsize(400, 200)  # 添加最小窗口限制

        # 配置主题样式
        self.setup_styles()

        self.topmost_var = tk.BooleanVar(value=True)

        # 控制区
        control_frame = ttk.Frame(root, style="Control.TFrame")
        control_frame.pack(fill="x", padx=10, pady=8)  # 减小边距

        add_button = ttk.Button(
            control_frame,
            text="添加秒表",
            command=self.add_stopwatch,
            style="Primary.TButton"
        )
        add_button.pack(side="left", padx=6)  # 减小边距

        ttk.Checkbutton(
            control_frame,
            text="窗口置顶",
            variable=self.topmost_var,
            command=self.toggle_topmost,
            style="Switch.TCheckbutton"
        ).pack(side="left", padx=6)  # 减小边距

        # 秒表容器
        self.container = ttk.Frame(root, style="Container.TFrame")
        self.container.pack(fill="both", expand=True, padx=5, pady=5)

        self.stopwatches = []
        self.add_stopwatch()

    def setup_styles(self):
        style = ttk.Style()
        
        # 配置通用样式
        style.configure("TFrame", background="#ffffff")
        style.configure("Control.TFrame", background="#ffffff")
        style.configure("Container.TFrame", background="#ffffff")
        
        # 配置按钮样式
        style.configure("Primary.TButton",
                       padding=3,  # 减小内边距
                       font=("Helvetica", 10))
        
        style.configure("Action.TButton",
                       padding=3,  # 减小内边距
                       font=("Helvetica", 10))
        
        style.configure("Secondary.TButton",
                       padding=3,  # 减小内边距
                       font=("Helvetica", 10))
        
        style.configure("Danger.TButton",
                       padding=3,  # 减小内边距
                       font=("Helvetica", 10))
        
        # 配置标签样式
        style.configure("Timer.TLabel",
                       font=("Helvetica", 12),  # 调小字体
                       background="#f0f0f0")
        
        # 配置复选框样式
        style.configure("Switch.TCheckbutton",
                       font=("Helvetica", 10),
                       background="#ffffff")

    def add_stopwatch(self):
        sw = Stopwatch(self.container, self.remove_stopwatch)
        self.stopwatches.append(sw)
        # 强制更新容器布局
        self.container.update_idletasks()
        self.root.update_idletasks()

    def remove_stopwatch(self, sw):
        if sw in self.stopwatches:
            self.stopwatches.remove(sw)

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())


def main():
    root = tk.Tk()
    app = StopwatchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
