"""
示例站点书籍爬虫占位模块。

仅用于保持旧代码的 import 路径可用；所有方法都会抛出 NotImplementedError，
提示用户需要自行实现真实爬虫或改用通用下载器。
"""


class ExampleSiteBookCrawler:
    """示例站点书籍爬虫（占位实现）。"""

    def __init__(self, *args, **kwargs):
        self.delay_between_requests = 2000
        self.retry_count = 3

    async def crawl_category(self, *args, **kwargs):
        raise NotImplementedError(
            "crawl_category() 尚未实现。ExampleSiteBookCrawler 是占位类，"
            "请根据目标站点的合规要求自行实现爬虫逻辑，或使用项目提供的通用下载器配置。"
        )

    def _not_implemented(self, method_name, *args, **kwargs):
        raise NotImplementedError(
            f"{method_name}() 尚未实现。ExampleSiteBookCrawler 是占位类，"
            "请根据目标站点的合规要求自行实现爬虫逻辑，或使用项目提供的通用下载器配置。"
        )

    def __getattr__(self, name):
        return lambda *args, **kwargs: self._not_implemented(name, *args, **kwargs)
