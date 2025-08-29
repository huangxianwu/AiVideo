import pandas as pd
import os
import glob
from datetime import datetime
import logging

class CSVProcessor:
    def __init__(self, csv_dir="images/csv", output_dir="images/csvdb"):
        self.csv_dir = csv_dir
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "imgdb.csv")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def read_csv_files(self):
        """读取所有CSV文件并提取关键字段"""
        all_data = []
        csv_files = glob.glob(os.path.join(self.csv_dir, "*.csv"))
        
        self.logger.info(f"找到 {len(csv_files)} 个CSV文件")
        
        for csv_file in csv_files:
            try:
                self.logger.info(f"处理文件: {csv_file}")
                df = pd.read_csv(csv_file, encoding='utf-8')
                
                # 提取关键字段
                for _, row in df.iterrows():
                    # 根据之前分析的CSV结构提取字段
                    product_id = row.get('产品ID', '')
                    product_name = row.get('产品名称', '')
                    main_image_url = row.get('产品主图url', '')
                    
                    # 如果产品主图url包含多个URL，只取第一个
                    if isinstance(main_image_url, str) and ',' in main_image_url:
                        main_image_url = main_image_url.split(',')[0].strip()
                    
                    # 创建时间使用文件修改时间
                    creation_time = datetime.fromtimestamp(os.path.getmtime(csv_file)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 只处理有效的产品ID
                    if product_id and str(product_id).strip():
                        all_data.append({
                            'product_id': str(product_id).strip(),
                            'product_name': str(product_name).strip(),
                            'main_image_url': str(main_image_url).strip(),
                            'creation_time': creation_time
                        })
                        
            except Exception as e:
                self.logger.error(f"处理文件 {csv_file} 时出错: {e}")
                continue
        
        return all_data
    
    def remove_duplicates(self, data):
        """去除重复的产品ID，只保留第一条记录"""
        seen_ids = set()
        unique_data = []
        
        for item in data:
            product_id = item['product_id']
            if product_id not in seen_ids:
                seen_ids.add(product_id)
                unique_data.append(item)
            else:
                self.logger.info(f"跳过重复的产品ID: {product_id}")
        
        self.logger.info(f"去重前: {len(data)} 条记录，去重后: {len(unique_data)} 条记录")
        return unique_data
    
    def save_to_imgdb(self, data):
        """保存数据到imgdb.csv"""
        if not data:
            self.logger.warning("没有数据需要保存")
            return
        
        df = pd.DataFrame(data)
        # 按创建时间倒序排列
        df = df.sort_values('creation_time', ascending=False)
        
        # 保存到CSV文件
        df.to_csv(self.output_file, index=False, encoding='utf-8')
        self.logger.info(f"数据已保存到: {self.output_file}")
        self.logger.info(f"共保存 {len(data)} 条记录")
    
    def cleanup_csv_files(self):
        """删除原始CSV文件"""
        csv_files = glob.glob(os.path.join(self.csv_dir, "*.csv"))
        
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                self.logger.info(f"已删除文件: {csv_file}")
            except Exception as e:
                self.logger.error(f"删除文件 {csv_file} 时出错: {e}")
    
    def process_all(self):
        """执行完整的处理流程"""
        self.logger.info("开始处理CSV文件...")
        
        # 1. 读取所有CSV文件
        all_data = self.read_csv_files()
        
        if not all_data:
            self.logger.warning("没有找到有效数据")
            return
        
        # 2. 去重处理
        unique_data = self.remove_duplicates(all_data)
        
        # 3. 保存到imgdb.csv
        self.save_to_imgdb(unique_data)
        
        # 4. 清理原始CSV文件
        self.cleanup_csv_files()
        
        self.logger.info("CSV处理完成！")
        return unique_data

if __name__ == "__main__":
    processor = CSVProcessor()
    processor.process_all()