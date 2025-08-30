"""
统一爬虫服务入口：对外暴露下载器、章节提取器与配置管理器。
路径：backend/crawlers/services
"""

from .config_manager import ConfigManager  # noqa: F401
from .chapter_extractor import ChapterExtractor  # noqa: F401
from .downloader import UniversalNovelDownloader  # noqa: F401

__all__ = ["ConfigManager", "ChapterExtractor", "UniversalNovelDownloader"]


