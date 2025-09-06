import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import hashlib
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class FileIndexManager:
    """文件索引管理器 - 管理output目录中的图片和视频文件索引"""
    
    def __init__(self, output_dir: str = "./output", index_file: str = "data/file_index.json"):
        self.output_dir = Path(output_dir)
        self.index_file_path = Path(index_file)
        self.thumbnail_dir = Path("./output/thumbnails")
        self._lock = threading.Lock()
        self._index_cache = None
        
        # 确保目录存在
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件类型
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
    def load_index(self) -> Dict[str, Any]:
        """加载文件索引"""
        if self._index_cache is not None:
            return self._index_cache
            
        try:
            if self.index_file_path.exists():
                with open(self.index_file_path, 'r', encoding='utf-8') as f:
                    self._index_cache = json.load(f)
            else:
                self._index_cache = self._create_empty_index()
        except (json.JSONDecodeError, IOError):
            self._index_cache = self._create_empty_index()
            
        return self._index_cache
    
    def _create_empty_index(self) -> Dict[str, Any]:
        """创建空的索引结构"""
        return {
            'files': {},  # 文件ID -> 文件信息
            'by_date': {},  # 日期 -> 文件ID列表
            'by_type': {'image': [], 'video': []},  # 类型 -> 文件ID列表
            'by_workflow': {},  # 工作流类型 -> 文件ID列表
            'metadata': {
                'last_scan': None,
                'total_files': 0,
                'total_size': 0
            }
        }
    
    def save_index(self, index: Dict[str, Any] = None) -> bool:
        """保存文件索引"""
        if index is None:
            index = self._index_cache
            
        try:
            with self._lock:
                # 确保目录存在
                self.index_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.index_file_path, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
                
                self._index_cache = index
                return True
        except IOError as e:
            print(f"保存索引失败: {e}")
            return False
    
    def _generate_file_id(self, file_path: Path) -> str:
        """生成文件唯一ID"""
        # 使用相对路径的MD5作为文件ID
        relative_path = file_path.relative_to(self.output_dir)
        return hashlib.md5(str(relative_path).encode()).hexdigest()[:16]
    
    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型"""
        ext = file_path.suffix.lower()
        if ext in self.image_extensions:
            return 'image'
        elif ext in self.video_extensions:
            return 'video'
        return 'other'
    
    def _extract_date_from_path(self, file_path: Path) -> str:
        """从文件路径提取日期"""
        # 假设路径格式为 output/MMDD/type/filename
        parts = file_path.parts
        for part in parts:
            if len(part) == 4 and part.isdigit():
                # 转换MMDD格式为YYYY-MM-DD
                month = part[:2]
                day = part[2:]
                year = datetime.now().year
                try:
                    return f"{year}-{month}-{day}"
                except ValueError:
                    pass
        
        # 如果无法从路径提取，使用文件修改时间
        return datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d')
    
    def _generate_thumbnail(self, file_path: Path, file_id: str) -> Optional[str]:
        """生成缩略图"""
        file_type = self._get_file_type(file_path)
        if file_type not in ['image', 'video']:
            return None
            
        try:
            # 使用原文件名（不含扩展名）+ _thumb.jpg
            original_name = file_path.stem
            thumbnail_path = self.thumbnail_dir / f"{original_name}_thumb.jpg"
            
            # 如果缩略图已存在，直接返回
            if thumbnail_path.exists():
                return str(thumbnail_path.relative_to(Path('.')))
            
            # 根据文件类型生成缩略图
            if file_type == 'image':
                return self._generate_image_thumbnail(file_path, thumbnail_path)
            elif file_type == 'video':
                return self._generate_video_thumbnail(file_path, thumbnail_path)
                
            return None
        except Exception as e:
            print(f"生成缩略图失败 {file_path}: {e}")
            return None
    
    def _generate_image_thumbnail(self, image_path: Path, thumbnail_path: Path) -> Optional[str]:
        """生成图片缩略图"""
        if not PIL_AVAILABLE:
            print("PIL未安装，跳过图片缩略图生成")
            return None
            
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 生成缩略图（保持宽高比）
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # 保存缩略图
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                
            return str(thumbnail_path.relative_to(Path('.')))
            
        except Exception as e:
            print(f"生成图片缩略图失败 {image_path}: {e}")
            return None
    
    def _generate_video_thumbnail(self, video_path: Path, thumbnail_path: Path) -> Optional[str]:
        """生成视频缩略图"""
        if not CV2_AVAILABLE:
            print("OpenCV未安装，跳过视频缩略图生成")
            return None
            
        try:
            # 使用OpenCV读取视频
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                print(f"无法打开视频文件: {video_path}")
                return None
            
            # 获取视频总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 跳转到视频中间位置
            middle_frame = total_frames // 2 if total_frames > 0 else 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            # 读取帧
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                print(f"无法读取视频帧: {video_path}")
                return None
            
            # 转换颜色空间（BGR to RGB）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL图像并生成缩略图
            if PIL_AVAILABLE:
                pil_image = Image.fromarray(frame_rgb)
                pil_image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                pil_image.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            else:
                # 如果PIL不可用，使用OpenCV保存
                # 调整大小
                height, width = frame.shape[:2]
                max_size = 300
                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)
                
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                cv2.imwrite(str(thumbnail_path), resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            return str(thumbnail_path.relative_to(Path('.')))
            
        except Exception as e:
            print(f"生成视频缩略图失败 {video_path}: {e}")
            return None
    
    def index_file(self, file_path: Path, task_id: str = None, workflow_type: str = None) -> bool:
        """索引单个文件"""
        if not file_path.exists() or not file_path.is_file():
            return False
            
        file_type = self._get_file_type(file_path)
        if file_type == 'other':
            return False
            
        index = self.load_index()
        file_id = self._generate_file_id(file_path)
        
        # 文件信息
        file_info = {
            'id': file_id,
            'path': str(file_path.relative_to(Path('.'))),
            'name': file_path.name,
            'type': file_type,
            'size': file_path.stat().st_size,
            'created_date': self._extract_date_from_path(file_path),
            'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'task_id': task_id,
            'workflow_type': workflow_type or 'unknown',
            'thumbnail': None
        }
        
        # 生成缩略图
        if file_type in ['image', 'video']:
            file_info['thumbnail'] = self._generate_thumbnail(file_path, file_id)
        
        # 更新索引
        with self._lock:
            index['files'][file_id] = file_info
            
            # 按日期索引
            date_key = file_info['created_date']
            if date_key not in index['by_date']:
                index['by_date'][date_key] = []
            if file_id not in index['by_date'][date_key]:
                index['by_date'][date_key].append(file_id)
            
            # 按类型索引
            if file_id not in index['by_type'][file_type]:
                index['by_type'][file_type].append(file_id)
            
            # 按工作流索引
            workflow_key = file_info['workflow_type']
            if workflow_key not in index['by_workflow']:
                index['by_workflow'][workflow_key] = []
            if file_id not in index['by_workflow'][workflow_key]:
                index['by_workflow'][workflow_key].append(file_id)
            
            # 更新元数据
            index['metadata']['total_files'] = len(index['files'])
            index['metadata']['total_size'] = sum(f['size'] for f in index['files'].values())
            index['metadata']['last_scan'] = datetime.now().isoformat()
        
        return self.save_index(index)
    
    def scan_output_directory(self, force_rescan: bool = False) -> Dict[str, int]:
        """扫描output目录，建立完整索引"""
        index = self.load_index() if not force_rescan else self._create_empty_index()
        
        stats = {'new_files': 0, 'updated_files': 0, 'total_files': 0}
        
        if not self.output_dir.exists():
            return stats
        
        # 扫描所有文件
        for file_path in self.output_dir.rglob('*'):
            if not file_path.is_file():
                continue
                
            file_type = self._get_file_type(file_path)
            if file_type == 'other':
                continue
            
            file_id = self._generate_file_id(file_path)
            
            # 检查是否需要更新
            if file_id in index['files']:
                existing_info = index['files'][file_id]
                current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                if existing_info['modified_time'] == current_mtime:
                    stats['total_files'] += 1
                    continue
                stats['updated_files'] += 1
            else:
                stats['new_files'] += 1
            
            # 索引文件
            self.index_file(file_path)
            stats['total_files'] += 1
        
        return stats
    
    def get_recent_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的文件"""
        index = self.load_index()
        files = list(index['files'].values())
        
        # 按修改时间排序
        files.sort(key=lambda x: x['modified_time'], reverse=True)
        
        return files[:limit]
    
    def get_files_by_date(self, date: str) -> List[Dict[str, Any]]:
        """按日期获取文件"""
        index = self.load_index()
        
        if date not in index['by_date']:
            return []
        
        file_ids = index['by_date'][date]
        return [index['files'][file_id] for file_id in file_ids if file_id in index['files']]
    
    def search_files(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索文件"""
        if filters is None:
            filters = {}
            
        index = self.load_index()
        results = []
        
        # 获取所有文件或根据筛选条件获取文件ID列表
        file_ids = set(index['files'].keys())
        
        # 按日期筛选
        if 'date_range' in filters and filters['date_range']:
            date_range = filters['date_range']
            date_file_ids = set()
            for date, ids in index['by_date'].items():
                if date_range['start'] <= date <= date_range['end']:
                    date_file_ids.update(ids)
            file_ids &= date_file_ids
        
        # 按类型筛选
        if 'file_type' in filters and filters['file_type']:
            type_file_ids = set(index['by_type'].get(filters['file_type'], []))
            file_ids &= type_file_ids
        
        # 按工作流筛选
        if 'workflow_type' in filters and filters['workflow_type']:
            workflow_file_ids = set(index['by_workflow'].get(filters['workflow_type'], []))
            file_ids &= workflow_file_ids
        
        # 按关键词搜索
        if 'keyword' in filters and filters['keyword']:
            keyword = filters['keyword'].lower()
            keyword_file_ids = set()
            for file_id, file_info in index['files'].items():
                if (keyword in file_info['name'].lower() or 
                    keyword in file_info.get('task_id', '').lower()):
                    keyword_file_ids.add(file_id)
            file_ids &= keyword_file_ids
        
        # 构建结果
        for file_id in file_ids:
            if file_id in index['files']:
                results.append(index['files'][file_id])
        
        # 排序
        sort_by = filters.get('sort_by', 'modified_time')
        reverse = filters.get('sort_desc', True)
        
        if sort_by in ['modified_time', 'created_date']:
            results.sort(key=lambda x: x[sort_by], reverse=reverse)
        elif sort_by == 'name':
            results.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        elif sort_by == 'size':
            results.sort(key=lambda x: x['size'], reverse=reverse)
        
        # 分页
        page = filters.get('page', 1)
        per_page = filters.get('per_page', 20)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return results[start_idx:end_idx]
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        index = self.load_index()
        return index['files'].get(file_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        index = self.load_index()
        
        stats = {
            'total_files': len(index['files']),
            'total_size': sum(f['size'] for f in index['files'].values()),
            'by_type': {},
            'by_date': {},
            'by_workflow': {},
            'last_scan': index['metadata'].get('last_scan')
        }
        
        # 按类型统计
        for file_type, file_ids in index['by_type'].items():
            stats['by_type'][file_type] = len(file_ids)
        
        # 按日期统计
        for date, file_ids in index['by_date'].items():
            stats['by_date'][date] = len(file_ids)
        
        # 按工作流统计
        for workflow, file_ids in index['by_workflow'].items():
            stats['by_workflow'][workflow] = len(file_ids)
        
        return stats
    
    def delete_file_index(self, file_id: str) -> bool:
        """删除文件索引（不删除实际文件）"""
        index = self.load_index()
        
        if file_id not in index['files']:
            return False
        
        file_info = index['files'][file_id]
        
        with self._lock:
            # 从主索引删除
            del index['files'][file_id]
            
            # 从各个分类索引中删除
            date_key = file_info['created_date']
            if date_key in index['by_date'] and file_id in index['by_date'][date_key]:
                index['by_date'][date_key].remove(file_id)
                if not index['by_date'][date_key]:
                    del index['by_date'][date_key]
            
            file_type = file_info['type']
            if file_id in index['by_type'][file_type]:
                index['by_type'][file_type].remove(file_id)
            
            workflow_type = file_info['workflow_type']
            if workflow_type in index['by_workflow'] and file_id in index['by_workflow'][workflow_type]:
                index['by_workflow'][workflow_type].remove(file_id)
                if not index['by_workflow'][workflow_type]:
                    del index['by_workflow'][workflow_type]
            
            # 删除缩略图
            if file_info.get('thumbnail'):
                thumbnail_path = Path(file_info['thumbnail'])
                if thumbnail_path.exists():
                    try:
                        thumbnail_path.unlink()
                    except OSError:
                        pass
            
            # 更新元数据
            index['metadata']['total_files'] = len(index['files'])
            index['metadata']['total_size'] = sum(f['size'] for f in index['files'].values())
        
        return self.save_index(index)
    
    def clear_index(self) -> bool:
        """清空文件索引"""
        try:
            with self._lock:
                # 创建空索引
                empty_index = self._create_empty_index()
                
                # 删除所有缩略图
                if self.thumbnail_dir.exists():
                    for thumbnail_file in self.thumbnail_dir.glob('*_thumb.jpg'):
                        try:
                            thumbnail_file.unlink()
                        except OSError:
                            pass
                
                # 保存空索引
                self._index_cache = empty_index
                return self.save_index(empty_index)
        except Exception as e:
            print(f"清空文件索引失败: {e}")
            return False
    
    def rebuild_index(self) -> Dict[str, int]:
        """重建整个文件索引"""
        try:
            self.clear_index()
            stats = self.scan_output_directory(force_rescan=True)
            print("文件索引重建完成")
            return stats
        except Exception as e:
            print(f"重建文件索引失败: {e}")
            return {'new_files': 0, 'updated_files': 0, 'total_files': 0}