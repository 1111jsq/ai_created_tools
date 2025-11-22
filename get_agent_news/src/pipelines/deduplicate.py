from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Iterable, List, Set

from src.models import NewsItem

log = logging.getLogger("dedup")


class LRUDeduplicator:
    """基于LRU缓存的内存去重器"""
    
    def __init__(self, cache_capacity: int = 1000):
        self.cache_capacity = cache_capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def is_duplicate(self, url_hash: str) -> bool:
        """检查URL哈希是否重复
        
        Args:
            url_hash: URL哈希值
            
        Returns:
            是否重复
        """
        if url_hash in self.cache:
            # 命中，移动到末尾（最近使用）
            self.cache.move_to_end(url_hash)
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False
    
    def add_url_hash(self, url_hash: str) -> None:
        """添加URL哈希到缓存
        
        Args:
            url_hash: URL哈希值
        """
        if url_hash in self.cache:
            # 已存在，移动到末尾
            self.cache.move_to_end(url_hash)
        else:
            # 新条目，添加到末尾
            self.cache[url_hash] = True
            
            # 检查是否需要淘汰
            if len(self.cache) > self.cache_capacity:
                # 淘汰最久未使用的条目
                self.cache.popitem(last=False)
                self.evictions += 1
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "cache_size": len(self.cache),
            "cache_capacity": self.cache_capacity,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


# 全局LRU去重器实例
_lru_deduplicator = LRUDeduplicator()


def deduplicate_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    """使用LRU缓存进行去重"""
    unique: List[NewsItem] = []
    duplicates = 0
    
    for item in items:
        item.ensure_hash()
        
        if _lru_deduplicator.is_duplicate(item.url_hash):
            duplicates += 1
            continue
        
        # 添加到缓存
        _lru_deduplicator.add_url_hash(item.url_hash)
        unique.append(item)
    
    # 获取缓存统计
    cache_stats = _lru_deduplicator.get_cache_stats()
    
    log.info(
        "去重: 原始=%s 唯一=%s 重复=%s 缓存大小=%s/%s 命中率=%.2f%%",
        len(unique) + duplicates,
        len(unique),
        duplicates,
        cache_stats["cache_size"],
        cache_stats["cache_capacity"],
        cache_stats["hit_rate"] * 100
    )
    
    return unique


def get_deduplication_stats() -> dict:
    """获取去重统计信息"""
    return _lru_deduplicator.get_cache_stats()
