from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FileOperationStats:
    """文件操作统计信息"""
    write_count: int = 0
    read_count: int = 0
    delete_count: int = 0
    total_bytes_written: int = 0
    total_bytes_read: int = 0
    operation_times: List[float] = None
    
    def __post_init__(self):
        if self.operation_times is None:
            self.operation_times = []
    
    def record_write(self, bytes_written: int, operation_time: float):
        """记录写入操作"""
        self.write_count += 1
        self.total_bytes_written += bytes_written
        self.operation_times.append(operation_time)
    
    def record_read(self, bytes_read: int, operation_time: float):
        """记录读取操作"""
        self.read_count += 1
        self.total_bytes_read += bytes_read
        self.operation_times.append(operation_time)
    
    def record_delete(self):
        """记录删除操作"""
        self.delete_count += 1
    
    @property
    def total_operations(self) -> int:
        """总操作次数"""
        return self.write_count + self.read_count + self.delete_count
    
    @property
    def avg_operation_time(self) -> float:
        """平均操作时间"""
        if not self.operation_times:
            return 0.0
        return sum(self.operation_times) / len(self.operation_times)
    
    @property
    def max_operation_time(self) -> float:
        """最大操作时间"""
        return max(self.operation_times) if self.operation_times else 0.0
    
    @property
    def min_operation_time(self) -> float:
        """最小操作时间"""
        return min(self.operation_times) if self.operation_times else 0.0


@dataclass
class DirectoryStats:
    """目录统计信息"""
    directory_path: str
    file_count: int = 0
    total_size_bytes: int = 0
    created_count: int = 0
    failed_count: int = 0


class FileStatsCollector:
    """文件统计收集器"""
    
    def __init__(self):
        self.file_stats = FileOperationStats()
        self.directory_stats: Dict[str, DirectoryStats] = defaultdict(
            lambda: DirectoryStats("")
        )
        self.start_time = datetime.now()
    
    def record_file_write(self, file_path: str, bytes_written: int, operation_time: float):
        """记录文件写入操作"""
        self.file_stats.record_write(bytes_written, operation_time)
        
        # 更新目录统计
        dir_path = os.path.dirname(file_path)
        if dir_path not in self.directory_stats:
            self.directory_stats[dir_path] = DirectoryStats(dir_path)
        
        self.directory_stats[dir_path].file_count += 1
        self.directory_stats[dir_path].total_size_bytes += bytes_written
    
    def record_file_read(self, file_path: str, bytes_read: int, operation_time: float):
        """记录文件读取操作"""
        self.file_stats.record_read(bytes_read, operation_time)
    
    def record_file_delete(self, file_path: str):
        """记录文件删除操作"""
        self.file_stats.record_delete()
    
    def record_directory_creation(self, dir_path: str, success: bool):
        """记录目录创建操作"""
        if dir_path not in self.directory_stats:
            self.directory_stats[dir_path] = DirectoryStats(dir_path)
        
        if success:
            self.directory_stats[dir_path].created_count += 1
        else:
            self.directory_stats[dir_path].failed_count += 1
    
    def get_summary(self) -> Dict[str, any]:
        """获取统计摘要"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "runtime_seconds": runtime,
            "total_operations": self.file_stats.total_operations,
            "write_operations": self.file_stats.write_count,
            "read_operations": self.file_stats.read_count,
            "delete_operations": self.file_stats.delete_count,
            "total_bytes_written": self.file_stats.total_bytes_written,
            "total_bytes_read": self.file_stats.total_bytes_read,
            "avg_operation_time": self.file_stats.avg_operation_time,
            "max_operation_time": self.file_stats.max_operation_time,
            "min_operation_time": self.file_stats.min_operation_time,
            "directory_count": len(self.directory_stats),
            "total_directories_created": sum(
                stats.created_count for stats in self.directory_stats.values()
            ),
            "total_directories_failed": sum(
                stats.failed_count for stats in self.directory_stats.values()
            ),
        }
    
    def get_detailed_stats(self) -> Dict[str, any]:
        """获取详细统计信息"""
        summary = self.get_summary()
        
        # 添加目录详细信息
        directory_details = {}
        for dir_path, stats in self.directory_stats.items():
            directory_details[dir_path] = {
                "file_count": stats.file_count,
                "total_size_bytes": stats.total_size_bytes,
                "created_count": stats.created_count,
                "failed_count": stats.failed_count,
            }
        
        summary["directory_details"] = directory_details
        return summary
    
    def reset(self):
        """重置统计信息"""
        self.file_stats = FileOperationStats()
        self.directory_stats.clear()
        self.start_time = datetime.now()
