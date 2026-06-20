"""
通用小说下载器占位模块。

仅用于保持旧代码的 import 路径可用；所有方法都会抛出 NotImplementedError，
提示用户需要自行实现真实下载逻辑或改用 crawlers.services.UniversalNovelDownloader。
"""


class UniversalNovelDownloader:
    """通用小说下载器（占位实现）。"""

    def __init__(self, *args, **kwargs):
        pass

    async def download_chapters(self, *args, **kwargs):
        raise NotImplementedError(
            "download_chapters() 尚未实现。pachong.universal_novel_downloader "
            "是占位模块，如需真实下载能力请使用 crawlers.services.UniversalNovelDownloader "
            "或自行实现合规下载逻辑。"
        )

    def _not_implemented(self, method_name, *args, **kwargs):
        raise NotImplementedError(
            f"{method_name}() 尚未实现。pachong.universal_novel_downloader 是占位模块，"
            "如需真实下载能力请使用 crawlers.services.UniversalNovelDownloader "
            "或自行实现合规下载逻辑。"
        )

    def __getattr__(self, name):
        return lambda *args, **kwargs: self._not_implemented(name, *args, **kwargs)
