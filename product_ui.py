import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import requests
from PIL import Image, ImageTk
from io import BytesIO
import os
from datetime import datetime
import threading
import re

class ProductUI:
    def __init__(self, root):
        self.root = root
        self.root.title("产品管理界面")
        self.root.geometry("1200x800")
        
        # 数据相关
        self.imgdb_file = "images/csvdb/imgdb.csv"
        self.data = []
        self.filtered_data = []
        self.current_page = 0
        self.items_per_page = 50
        self.selected_items = set()
        
        # 图片缓存
        self.image_cache = {}
        
        # 创建UI
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="产品数据管理", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 刷新按钮
        refresh_btn = ttk.Button(control_frame, text="刷新数据", command=self.load_data)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 全选/取消全选按钮
        select_all_btn = ttk.Button(control_frame, text="全选当前页", command=self.select_all_current_page)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_selection_btn = ttk.Button(control_frame, text="清除选择", command=self.clear_selection)
        clear_selection_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 确认和取消按钮
        confirm_btn = ttk.Button(control_frame, text="确认下载", command=self.confirm_download)
        confirm_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(control_frame, text="取消", command=self.cancel_selection)
        cancel_btn.pack(side=tk.RIGHT)
        
        # 表格框架
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview表格
        columns = ('选择', '产品ID', '产品名称', '主图', '创建时间')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.tree.heading('选择', text='选择')
        self.tree.heading('产品ID', text='产品ID')
        self.tree.heading('产品名称', text='产品名称')
        self.tree.heading('主图', text='主图')
        self.tree.heading('创建时间', text='创建时间')
        
        self.tree.column('选择', width=60, anchor='center')
        self.tree.column('产品ID', width=150, anchor='center')
        self.tree.column('产品名称', width=400, anchor='w')
        self.tree.column('主图', width=80, anchor='center')
        self.tree.column('创建时间', width=150, anchor='center')
        
        # 绑定点击事件
        self.tree.bind('<Button-1>', self.on_item_click)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局表格和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分页控制框架
        page_frame = ttk.Frame(main_frame)
        page_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 分页信息
        self.page_info_label = ttk.Label(page_frame, text="")
        self.page_info_label.pack(side=tk.LEFT)
        
        # 分页按钮
        ttk.Button(page_frame, text="上一页", command=self.prev_page).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(page_frame, text="下一页", command=self.next_page).pack(side=tk.RIGHT)
        
        # 页码输入
        ttk.Label(page_frame, text="跳转到第").pack(side=tk.RIGHT, padx=(10, 5))
        self.page_entry = ttk.Entry(page_frame, width=5)
        self.page_entry.pack(side=tk.RIGHT)
        self.page_entry.bind('<Return>', self.jump_to_page)
        ttk.Label(page_frame, text="页").pack(side=tk.RIGHT, padx=(5, 0))
        
        # 状态栏
        self.status_label = ttk.Label(main_frame, text="准备就绪")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
    def load_data(self):
        """加载数据"""
        try:
            if not os.path.exists(self.imgdb_file):
                messagebox.showerror("错误", f"数据文件不存在: {self.imgdb_file}")
                return
            
            df = pd.read_csv(self.imgdb_file)
            self.data = df.to_dict('records')
            self.filtered_data = self.data.copy()
            
            self.current_page = 0
            self.selected_items.clear()
            self.update_table()
            self.update_page_info()
            
            self.status_label.config(text=f"已加载 {len(self.data)} 条记录")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
    
    def update_table(self):
        """更新表格显示"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 计算当前页数据
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_data = self.filtered_data[start_idx:end_idx]
        
        # 插入数据
        for i, row in enumerate(page_data):
            item_id = start_idx + i
            is_selected = item_id in self.selected_items
            select_text = "✓" if is_selected else "○"
            
            # 截断产品名称
            product_name = row['product_name'][:50] + "..." if len(row['product_name']) > 50 else row['product_name']
            
            self.tree.insert('', 'end', iid=item_id, values=(
                select_text,
                row['product_id'],
                product_name,
                "图片",
                row['creation_time']
            ))
    
    def update_page_info(self):
        """更新分页信息"""
        total_pages = (len(self.filtered_data) - 1) // self.items_per_page + 1 if self.filtered_data else 0
        current_page_display = self.current_page + 1 if total_pages > 0 else 0
        
        info_text = f"第 {current_page_display} 页，共 {total_pages} 页 | 总计 {len(self.filtered_data)} 条记录 | 已选择 {len(self.selected_items)} 项"
        self.page_info_label.config(text=info_text)
    
    def on_item_click(self, event):
        """处理表格项点击事件"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if item and column == '#1':  # 点击选择列
                item_id = int(item)
                if item_id in self.selected_items:
                    self.selected_items.remove(item_id)
                else:
                    self.selected_items.add(item_id)
                
                self.update_table()
                self.update_page_info()
    
    def select_all_current_page(self):
        """选择当前页所有项目"""
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.filtered_data))
        
        for i in range(start_idx, end_idx):
            self.selected_items.add(i)
        
        self.update_table()
        self.update_page_info()
    
    def clear_selection(self):
        """清除所有选择"""
        self.selected_items.clear()
        self.update_table()
        self.update_page_info()
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()
            self.update_page_info()
    
    def next_page(self):
        """下一页"""
        total_pages = (len(self.filtered_data) - 1) // self.items_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()
            self.update_page_info()
    
    def jump_to_page(self, event):
        """跳转到指定页"""
        try:
            page_num = int(self.page_entry.get()) - 1
            total_pages = (len(self.filtered_data) - 1) // self.items_per_page + 1
            
            if 0 <= page_num < total_pages:
                self.current_page = page_num
                self.update_table()
                self.update_page_info()
            else:
                messagebox.showwarning("警告", f"页码超出范围 (1-{total_pages})")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的页码")
    
    def confirm_download(self):
        """确认下载选中的图片"""
        if not self.selected_items:
            messagebox.showwarning("警告", "请先选择要下载的项目")
            return
        
        # 确认对话框
        result = messagebox.askyesno("确认", f"确定要下载 {len(self.selected_items)} 个选中的图片吗？")
        if result:
            self.download_selected_images()
    
    def cancel_selection(self):
        """取消选择"""
        self.clear_selection()
    
    def download_selected_images(self):
        """下载选中的图片"""
        # 创建下载目录
        download_dir = "images/jpg"
        os.makedirs(download_dir, exist_ok=True)
        
        # 获取选中的数据
        selected_data = [self.filtered_data[i] for i in self.selected_items]
        
        # 在新线程中下载图片
        threading.Thread(target=self._download_images_thread, args=(selected_data, download_dir), daemon=True).start()
    
    def _download_images_thread(self, selected_data, download_dir):
        """在后台线程中下载图片"""
        success_count = 0
        total_count = len(selected_data)
        
        for i, item in enumerate(selected_data):
            try:
                # 更新状态
                self.root.after(0, lambda: self.status_label.config(text=f"正在下载 {i+1}/{total_count}: {item['product_name'][:30]}..."))
                
                # 生成文件名
                filename = self._generate_filename(item['product_name'])
                filepath = os.path.join(download_dir, filename)
                
                # 下载图片
                response = requests.get(item['main_image_url'], timeout=10)
                response.raise_for_status()
                
                # 保存图片
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                success_count += 1
                
            except Exception as e:
                print(f"下载失败 {item['product_name']}: {e}")
        
        # 下载完成
        self.root.after(0, lambda: self._download_complete(success_count, total_count))
    
    def _generate_filename(self, product_name):
        """生成文件名：MMDD+产品名称前3个单词"""
        # 获取当前月日
        now = datetime.now()
        mmdd = now.strftime("%m%d")
        
        # 提取产品名称前3个单词
        words = re.findall(r'\b\w+\b', product_name)
        first_three_words = '_'.join(words[:3]) if len(words) >= 3 else '_'.join(words)
        
        # 清理文件名中的特殊字符
        first_three_words = re.sub(r'[^\w\-_]', '', first_three_words)
        
        return f"{mmdd}_{first_three_words}.jpg"
    
    def _download_complete(self, success_count, total_count):
        """下载完成回调"""
        self.status_label.config(text=f"下载完成: {success_count}/{total_count} 成功")
        messagebox.showinfo("下载完成", f"成功下载 {success_count}/{total_count} 张图片")
        
        # 清除选择
        self.clear_selection()

def main():
    root = tk.Tk()
    app = ProductUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()