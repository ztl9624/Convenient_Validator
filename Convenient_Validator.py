import time
import pyotp
import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os
from pathlib import Path

class TOTPManagerPro:
    # ============================================================
    # 🎨 配置区域 - 所有可修改的内容都在这里
    # ============================================================
    CONFIG = {
        # 基础信息
        "app_name": "验证码管理器 Pro",
        "app_emoji": "🔐",
        "version": "v1.0",
        
        # 作者信息
        "author_name": "Courvif",  
        "twitter_username": "CengBaofu",  
        "github_username": "courvif", 
        
        # 链接
        "twitter_url": "https://twitter.com/CengBaofu", 
        "github_url": "https://github.com/courvif",  
        
        # 界面设置
        "window_width": 800,
        "window_height": 600,
        "items_per_page": 10,
        
        # 颜色主题
        "color_primary": "#3498db",      # 主色调
        "color_success": "#2ecc71",      # 成功色
        "color_danger": "#e74c3c",       # 危险色
        "color_header": "#2c3e50",       # 标题栏背景
        "color_footer": "#34495e",       # 底部栏背景
        "color_twitter": "#1DA1F2",      # 推特蓝
    }
    # ============================================================
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{self.CONFIG['app_emoji']} {self.CONFIG['app_name']} {self.CONFIG['version']}")
        self.root.geometry(f"{self.CONFIG['window_width']}x{self.CONFIG['window_height']}")
        self.root.minsize(600, 400)
        
        # UI就绪标志
        self._ui_ready = False
        
        # 配置文件路径
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        self.config_file = Path(application_path) / "accounts.json"
        print(f"[INFO] 程序路径: {application_path}")
        print(f"[INFO] 配置文件: {self.config_file}")
        
        # 数据
        self.accounts = []
        self.groups = {}
        self.filtered_accounts = []
        self.labels = []
        
        # 界面状态
        self.items_per_page = self.CONFIG['items_per_page']
        self.current_page = 0
        self.current_group = "全部"
        self.search_query = ""
        
        # 加载账户
        self.load_accounts()
        
        # 创建界面
        self.create_ui()
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 启动更新
        self.update_codes()
    
    def load_accounts(self):
        """从配置文件加载账户信息"""
        file_exists = self.config_file.exists()
        print(f"[DEBUG] 配置文件路径: {self.config_file}")
        print(f"[DEBUG] 文件是否存在: {file_exists}")
        
        if not file_exists:
            example_accounts = [
                {"name": "示例-Google", "secret": "JBSWY3DPEHPK3PXP", "group": "工作"},
                {"name": "示例-GitHub", "secret": "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ", "group": "工作"},
                {"name": "示例-微信", "secret": "", "group": "社交"},
                {"name": "示例-支付宝", "secret": "", "group": "金融"},
            ]
            try:
                self.save_accounts(example_accounts)
                self.accounts = example_accounts
                print(f"[DEBUG] 已创建示例配置文件")
                messagebox.showinfo(
                    f"欢迎使用 {self.CONFIG['app_name']}",
                    f"已创建示例配置文件：\n{self.config_file}\n\n"
                    f"请编辑此文件添加你的真实账户信息。\n\n"
                    f"作者: @{self.CONFIG['twitter_username']}"
                )
            except Exception as e:
                print(f"[DEBUG] 创建配置失败: {e}")
                messagebox.showerror("错误", f"创建配置文件失败：\n{e}")
                self.accounts = []
        else:
            print(f"[DEBUG] 开始读取现有配置文件...")
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        self.accounts = loaded_data
                        print(f"[DEBUG] 成功读取 {len(self.accounts)} 个账户")
                    else:
                        raise ValueError("配置文件格式错误：应该是一个账户列表")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON格式错误: {e}")
                messagebox.showerror("错误", f"配置文件JSON格式错误：\n{e}\n\n请检查文件格式是否正确。")
                self.accounts = []
            except Exception as e:
                print(f"[DEBUG] 读取失败: {e}")
                messagebox.showerror("错误", f"读取配置文件失败：\n{e}")
                self.accounts = []
        
        self.build_groups()
        self.apply_filters()
    
    def build_groups(self):
        """构建分组字典"""
        self.groups = {"全部": len(self.accounts)}
        for acc in self.accounts:
            group = acc.get("group", "未分组")
            if group not in self.groups:
                self.groups[group] = 0
            self.groups[group] += 1
    
    def apply_filters(self):
        """应用搜索和分组过滤"""
        filtered = self.accounts
        
        if self.current_group != "全部":
            filtered = [acc for acc in filtered if acc.get("group", "未分组") == self.current_group]
        
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                acc for acc in filtered
                if query in acc.get("name", "").lower() or 
                   query in acc.get("group", "").lower()
            ]
        
        self.filtered_accounts = filtered
    
    def save_accounts(self, accounts):
        """保存账户到配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败：\n{e}")
    
    def normalize_secret(self, s: str) -> str:
        """清洗密钥字符串"""
        return s.replace(" ", "").replace("-", "").upper()
    
    def create_ui(self):
        """创建用户界面"""
        # 顶部标题栏
        header_frame = tk.Frame(self.root, bg=self.CONFIG['color_header'], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # 标题容器（居中）
        title_container = tk.Frame(header_frame, bg=self.CONFIG['color_header'])
        title_container.pack(expand=True)
        
        # 主标题
        title_label = tk.Label(
            title_container,
            text=f"{self.CONFIG['app_emoji']} {self.CONFIG['app_name']}",
            font=("Arial", 16, "bold"),
            bg=self.CONFIG['color_header'],
            fg="white"
        )
        title_label.pack(side="left", padx=(0, 10))
        
        # 版本号
        version_label = tk.Label(
            title_container,
            text=self.CONFIG['version'],
            font=("Arial", 8),
            bg=self.CONFIG['color_header'],
            fg="#95a5a6"
        )
        version_label.pack(side="left", padx=(0, 15))
        
        # 工具栏
        toolbar_frame = tk.Frame(self.root, bg="#ecf0f1")
        toolbar_frame.pack(fill="x")
        
        left_tools = tk.Frame(toolbar_frame, bg="#ecf0f1")
        left_tools.pack(side="left", padx=10, pady=7)
        
        btn_style = {
            "font": ("Arial", 9),
            "cursor": "hand2",
            "relief": "flat",
            "bd": 0,
            "padx": 12,
            "pady": 5
        }
        
        refresh_btn = tk.Button(
            left_tools,
            text="🔄 刷新",
            command=self.reload_accounts,
            bg=self.CONFIG['color_primary'],
            fg="white",
            **btn_style
        )
        refresh_btn.pack(side="left", padx=5)
        
        edit_btn = tk.Button(
            left_tools,
            text="📝 编辑配置",
            command=self.open_config,
            bg=self.CONFIG['color_success'],
            fg="white",
            **btn_style
        )
        edit_btn.pack(side="left", padx=5)
        
        info_label = tk.Label(
            toolbar_frame,
            text=f"📁 {self.config_file.name}",
            font=("Arial", 8),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        info_label.pack(side="right", padx=10, pady=7)
        
        # 搜索和分组栏
        filter_frame = tk.Frame(self.root, bg="#f8f9fa")
        filter_frame.pack(fill="x", padx=10, pady=8)
        
        # 搜索框
        search_frame = tk.Frame(filter_frame, bg="#f8f9fa")
        search_frame.pack(side="left", fill="x", expand=True)
        
        search_label = tk.Label(
            search_frame,
            text="🔍",
            font=("Arial", 12),
            bg="#f8f9fa"
        )
        search_label.pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 10),
            relief="solid",
            bd=1,
            width=30
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "搜索账户名称或分组...")
        self.search_entry.config(fg="#95a5a6")
        
        def on_focus_in(event):
            if self.search_entry.get() == "搜索账户名称或分组...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(fg="black")
        
        def on_focus_out(event):
            if not self.search_entry.get():
                self.search_entry.insert(0, "搜索账户名称或分组...")
                self.search_entry.config(fg="#95a5a6")
        
        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)
        
        clear_btn = tk.Button(
            search_frame,
            text="✕",
            command=self.clear_search,
            font=("Arial", 10),
            bg=self.CONFIG['color_danger'],
            fg="white",
            cursor="hand2",
            relief="flat",
            bd=0,
            padx=8,
            pady=2
        )
        clear_btn.pack(side="left", padx=(5, 0))
        
        # 分组选择
        group_frame = tk.Frame(filter_frame, bg="#f8f9fa")
        group_frame.pack(side="right", padx=(10, 0))
        
        group_label = tk.Label(
            group_frame,
            text="📂 分组:",
            font=("Arial", 9),
            bg="#f8f9fa"
        )
        group_label.pack(side="left", padx=(0, 5))
        
        self.group_var = tk.StringVar(value="全部")
        self.group_combo = ttk.Combobox(
            group_frame,
            textvariable=self.group_var,
            values=list(self.groups.keys()),
            state="readonly",
            width=15,
            font=("Arial", 9)
        )
        self.group_combo.pack(side="left")
        self.group_combo.bind('<<ComboboxSelected>>', self.on_group_change)
        
        # 主容器
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f8f9fa", sashwidth=5)
        self.main_paned.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧分组列表
        left_frame = tk.Frame(self.main_paned, bg="white", width=180)
        self.main_paned.add(left_frame, minsize=150)
        
        group_header = tk.Label(
            left_frame,
            text="分组列表",
            font=("Arial", 10, "bold"),
            bg=self.CONFIG['color_footer'],
            fg="white",
            pady=8
        )
        group_header.pack(fill="x")
        
        group_canvas_frame = tk.Frame(left_frame, bg="white")
        group_canvas_frame.pack(fill="both", expand=True)
        
        group_scrollbar = tk.Scrollbar(group_canvas_frame, orient="vertical")
        group_scrollbar.pack(side="right", fill="y")
        
        self.group_listbox = tk.Listbox(
            group_canvas_frame,
            font=("Arial", 9),
            bg="white",
            fg="#2c3e50",
            selectmode="single",
            relief="flat",
            highlightthickness=0,
            yscrollcommand=group_scrollbar.set,
            activestyle="none"
        )
        self.group_listbox.pack(side="left", fill="both", expand=True)
        group_scrollbar.config(command=self.group_listbox.yview)
        
        self.group_listbox.bind('<<ListboxSelect>>', self.on_group_list_select)
        
        self.update_group_list()
        
        # 右侧账户列表
        right_frame = tk.Frame(self.main_paned, bg="#f8f9fa")
        self.main_paned.add(right_frame, minsize=400)
        
        self.stats_label = tk.Label(
            right_frame,
            text="",
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#7f8c8d",
            anchor="w"
        )
        self.stats_label.pack(fill="x", padx=5, pady=(0, 5))
        
        list_canvas_frame = tk.Frame(right_frame, bg="#f8f9fa")
        list_canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(list_canvas_frame, bg="#f8f9fa", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.container = tk.Frame(self.canvas, bg="#f8f9fa")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        
        self.container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 底部分页栏
        bottom_frame = tk.Frame(self.root, bg="#ecf0f1", height=50)
        bottom_frame.pack(fill="x")
        bottom_frame.pack_propagate(False)
        
        nav_frame = tk.Frame(bottom_frame, bg="#ecf0f1")
        nav_frame.pack(pady=10)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="⬅ 上一页",
            command=self.prev_page,
            font=("Arial", 9),
            bg="#95a5a6",
            fg="white",
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_info_label = tk.Label(
            nav_frame,
            text="",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.page_info_label.pack(side="left", padx=15)
        
        self.next_btn = tk.Button(
            nav_frame,
            text="下一页 ➡",
            command=self.next_page,
            font=("Arial", 9),
            bg="#95a5a6",
            fg="white",
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5
        )
        self.next_btn.pack(side="left", padx=5)
        
        # ✅ 底部作者信息栏
        footer_frame = tk.Frame(self.root, bg=self.CONFIG['color_footer'], height=35)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)
        
        footer_content = tk.Frame(footer_frame, bg=self.CONFIG['color_footer'])
        footer_content.pack(expand=True)
        
        # Made with ❤️
        made_label = tk.Label(
            footer_content,
            text="Made with ❤️ by",
            font=("Arial", 8),
            bg=self.CONFIG['color_footer'],
            fg="#95a5a6"
        )
        made_label.pack(side="left", padx=(0, 5))
        
        # 作者名字
        if self.CONFIG.get('author_name'):
            author_label = tk.Label(
                footer_content,
                text=self.CONFIG['author_name'],
                font=("Arial", 9, "bold"),
                bg=self.CONFIG['color_footer'],
                fg="#ecf0f1"
            )
            author_label.pack(side="left", padx=3)
        
        # 推特链接
        twitter_link = tk.Label(
            footer_content,
            text=f"@{self.CONFIG['twitter_username']}",
            font=("Arial", 9, "bold"),
            bg=self.CONFIG['color_footer'],
            fg=self.CONFIG['color_twitter'],
            cursor="hand2"
        )
        twitter_link.pack(side="left", padx=5)
        
        def open_twitter(event=None):
            import webbrowser
            webbrowser.open(self.CONFIG['twitter_url'])
        
        twitter_link.bind("<Button-1>", open_twitter)
        
        def on_twitter_enter(e):
            twitter_link.config(fg="#ffffff", font=("Arial", 9, "bold", "underline"))
        def on_twitter_leave(e):
            twitter_link.config(fg=self.CONFIG['color_twitter'], font=("Arial", 9, "bold"))
        
        twitter_link.bind("<Enter>", on_twitter_enter)
        twitter_link.bind("<Leave>", on_twitter_leave)
        
        # GitHub 链接（可选）
        if self.CONFIG.get('github_username') and self.CONFIG.get('github_url'):
            separator = tk.Label(
                footer_content,
                text="|",
                font=("Arial", 8),
                bg=self.CONFIG['color_footer'],
                fg="#7f8c8d"
            )
            separator.pack(side="left", padx=5)
            
            github_link = tk.Label(
                footer_content,
                text="⭐ GitHub",
                font=("Arial", 8),
                bg=self.CONFIG['color_footer'],
                fg="#95a5a6",
                cursor="hand2"
            )
            github_link.pack(side="left", padx=5)
            
            def open_github(event=None):
                import webbrowser
                webbrowser.open(self.CONFIG['github_url'])
            
            github_link.bind("<Button-1>", open_github)
            
            def on_github_enter(e):
                github_link.config(fg="#ffffff", font=("Arial", 8, "underline"))
            def on_github_leave(e):
                github_link.config(fg="#95a5a6", font=("Arial", 8))
            
            github_link.bind("<Enter>", on_github_enter)
            github_link.bind("<Leave>", on_github_leave)
        
        # 显示第一页
        self.show_page(0)
        
        # ✅ 在所有UI创建完成后再绑定事件
        self.search_var.trace('w', self.on_search_change)
        
        # ✅ 标记UI已就绪
        self._ui_ready = True
    
    def update_group_list(self):
        """更新分组列表"""
        self.group_listbox.delete(0, tk.END)
        for group, count in self.groups.items():
            self.group_listbox.insert(tk.END, f"{group} ({count})")
        
        group_list = list(self.groups.keys())
        if self.current_group in group_list:
            self.group_listbox.selection_clear(0, tk.END)
            self.group_listbox.selection_set(group_list.index(self.current_group))
    
    def on_group_list_select(self, event):
        """分组列表选择事件"""
        if not self._ui_ready:
            return
        
        selection = self.group_listbox.curselection()
        if selection:
            group_text = self.group_listbox.get(selection[0])
            group_name = group_text.split(" (")[0]
            self.current_group = group_name
            self.group_var.set(group_name)
            self.apply_filters()
            self.show_page(0)
    
    def on_group_change(self, event):
        """分组下拉框变化事件"""
        if not self._ui_ready:
            return
        
        self.current_group = self.group_var.get()
        self.apply_filters()
        self.show_page(0)
        self.update_group_list()
    
    def on_search_change(self, *args):
        """搜索框变化事件"""
        if not self._ui_ready:
            return
        
        search_text = self.search_var.get()
        if search_text == "搜索账户名称或分组...":
            self.search_query = ""
        else:
            self.search_query = search_text
        self.apply_filters()
        self.show_page(0)
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "搜索账户名称或分组...")
        self.search_entry.config(fg="#95a5a6")
        self.search_query = ""
        self.apply_filters()
        self.show_page(0)
    
    def on_canvas_configure(self, event):
        """Canvas 大小变化时调整内容宽度"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def on_window_resize(self, event):
        """窗口大小变化事件"""
        pass
    
    def show_page(self, page: int):
        """显示指定页码"""
        for widget in self.container.winfo_children():
            widget.destroy()
        self.labels.clear()
        
        total = len(self.filtered_accounts)
        group_text = f"分组: {self.current_group}" if self.current_group != "全部" else "全部账户"
        search_text = f" | 搜索: \"{self.search_query}\"" if self.search_query else ""
        self.stats_label.config(text=f"{group_text}{search_text} | 共 {total} 个账户")
        
        if not self.filtered_accounts:
            no_data_label = tk.Label(
                self.container,
                text="暂无匹配的账户\n\n请尝试其他搜索条件或分组",
                font=("Arial", 12),
                fg="#95a5a6",
                bg="#f8f9fa"
            )
            no_data_label.pack(expand=True, pady=50)
            self.current_page = 0
            self.update_page_buttons()
            return
        
        start = page * self.items_per_page
        end = start + self.items_per_page
        sub_accounts = self.filtered_accounts[start:end]
        
        for idx, acc in enumerate(sub_accounts):
            card = tk.Frame(
                self.container,
                bg="white",
                relief="solid",
                bd=1,
                highlightbackground="#dfe6e9",
                highlightthickness=1
            )
            card.pack(fill="x", padx=5, pady=4)
            
            content_frame = tk.Frame(card, bg="white")
            content_frame.pack(fill="x", padx=15, pady=10)
            
            left_info = tk.Frame(content_frame, bg="white")
            left_info.grid(row=0, column=0, sticky="w", padx=(0, 20))
            
            name_label = tk.Label(
                left_info,
                text=acc.get('name', '未命名'),
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#2c3e50",
                anchor="w"
            )
            name_label.pack(anchor="w")
            
            group_tag = tk.Label(
                left_info,
                text=f"📂 {acc.get('group', '未分组')}",
                font=("Arial", 8),
                bg="#ecf0f1",
                fg="#7f8c8d",
                padx=6,
                pady=2
            )
            group_tag.pack(anchor="w", pady=(3, 0))
            
            code_label = tk.Label(
                content_frame,
                text="------",
                font=("Consolas", 18, "bold"),
                bg="white",
                fg=self.CONFIG['color_primary'],
                cursor="hand2"
            )
            code_label.grid(row=0, column=1, padx=20)
            
            time_label = tk.Label(
                content_frame,
                text="--s",
                font=("Arial", 10),
                bg="white",
                fg=self.CONFIG['color_danger'],
                width=5
            )
            time_label.grid(row=0, column=2, padx=5)
            
            tip_label = tk.Label(
                content_frame,
                text="",
                font=("Arial", 9),
                bg="white",
                fg=self.CONFIG['color_success']
            )
            tip_label.grid(row=0, column=3, padx=10)
            
            secret = acc.get("secret", "") or ""
            secret_norm = self.normalize_secret(secret)
            totp_obj = None
            
            if secret_norm:
                try:
                    totp_obj = pyotp.TOTP(secret_norm)
                except Exception:
                    code_label.config(text="密钥错误", fg=self.CONFIG['color_danger'])
            
            def make_copy_func(label_ref, tip_ref):
                def _copy(event=None):
                    code_text = label_ref.cget("text")
                    if not code_text or "------" in code_text or "错误" in code_text:
                        return
                    self.root.clipboard_clear()
                    self.root.clipboard_append(code_text)
                    tip_ref.config(text="✓ 已复制")
                    self.root.after(1500, lambda: tip_ref.config(text=""))
                return _copy
            
            copy_action = make_copy_func(code_label, tip_label)
            code_label.bind("<Button-1>", copy_action)
            
            def on_enter(e):
                code_label.config(bg="#ecf0f1")
            def on_leave(e):
                code_label.config(bg="white")
            
            code_label.bind("<Enter>", on_enter)
            code_label.bind("<Leave>", on_leave)
            
            self.labels.append((code_label, time_label, totp_obj, tip_label))
        
        self.current_page = page
        self.update_page_buttons()
        self.canvas.yview_moveto(0)
    
    def update_page_buttons(self):
        """更新分页按钮状态"""
        if not self.filtered_accounts:
            self.page_info_label.config(text="0/0 页")
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return
        
        total_pages = (len(self.filtered_accounts) - 1) // self.items_per_page + 1
        self.page_info_label.config(text=f"{self.current_page + 1}/{total_pages} 页")
        
        self.prev_btn.config(
            state="normal" if self.current_page > 0 else "disabled",
            bg=self.CONFIG['color_primary'] if self.current_page > 0 else "#95a5a6"
        )
        self.next_btn.config(
            state="normal" if self.current_page < total_pages - 1 else "disabled",
            bg=self.CONFIG['color_primary'] if self.current_page < total_pages - 1 else "#95a5a6"
        )
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def next_page(self):
        """下一页"""
        total_pages = (len(self.filtered_accounts) - 1) // self.items_per_page + 1
        if self.current_page < total_pages - 1:
            self.show_page(self.current_page + 1)
    
    def update_codes(self):
        """更新所有验证码"""
        now = int(time.time())
        
        for code_label, time_label, totp, tip_label in self.labels:
            if totp is None:
                if "错误" not in code_label.cget("text"):
                    code_label.config(text="------", fg="#95a5a6")
                time_label.config(text="--s")
            else:
                try:
                    code = totp.now()
                    remain = totp.interval - (now % totp.interval)
                    code_label.config(text=code, fg=self.CONFIG['color_primary'])
                    time_label.config(
                        text=f"{remain}s",
                        fg=self.CONFIG['color_danger'] if remain <= 5 else "#f39c12" if remain <= 10 else self.CONFIG['color_success']
                    )
                except Exception:
                    code_label.config(text="生成失败", fg=self.CONFIG['color_danger'])
                    time_label.config(text="--s")
        
        self.root.after(1000, self.update_codes)
    
    def reload_accounts(self):
        """重新加载账户"""
        old_page = self.current_page
        
        self.load_accounts()
        self.group_combo['values'] = list(self.groups.keys())
        self.update_group_list()
        
        total_pages = (len(self.filtered_accounts) - 1) // self.items_per_page + 1 if self.filtered_accounts else 1
        new_page = min(old_page, total_pages - 1) if total_pages > 0 else 0
        
        self.show_page(new_page)
        
        messagebox.showinfo(
            "重新加载成功", 
            f"已从配置文件加载 {len(self.accounts)} 个账户\n分组数量: {len(self.groups) - 1}"
        )
    
    def open_config(self):
        """打开配置文件"""
        import platform
        import subprocess
        
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(self.config_file)
            elif system == "Darwin":
                subprocess.run(["open", self.config_file])
            else:
                subprocess.run(["xdg-open", self.config_file])
            
            messagebox.showinfo(
                "提示",
                "已打开配置文件\n\n编辑完成后请点击「刷新」按钮重新加载"
            )
        except Exception as e:
            messagebox.showerror("错误", f"无法打开配置文件：\n{e}")


def main():
    root = tk.Tk()
    app = TOTPManagerPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
