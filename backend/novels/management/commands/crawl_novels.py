from django.core.management.base import BaseCommand
from django.utils import timezone
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from hetushu_quick_crawler import HetuShuQuickCrawler
from hetushu_book_crawler import HetuShuBookCrawler
from universal_novel_downloader import UniversalNovelDownloader
from novels.models import Novel, Chapter, NovelSource, NovelSourceRelation


class Command(BaseCommand):
    help = '使用新的pachong爬虫系统爬取小说数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['quick', 'book', 'universal'],
            default='quick',
            help='爬虫类型: quick(快速爬取), book(详细爬取), universal(通用下载器)'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='爬取的分类（仅适用于quick类型）'
        )
        parser.add_argument(
            '--book-id',
            type=str,
            help='书籍ID（适用于book和universal类型）'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='爬取数量限制'
        )

    def handle(self, *args, **options):
        crawler_type = options['type']
        
        try:
            if crawler_type == 'quick':
                self.run_quick_crawler(options)
            elif crawler_type == 'book':
                self.run_book_crawler(options)
            elif crawler_type == 'universal':
                self.run_universal_crawler(options)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'爬虫执行失败: {str(e)}')
            )

    def run_quick_crawler(self, options):
        """运行快速爬虫"""
        self.stdout.write('启动快速爬虫...')
        
        import asyncio
        from playwright.async_api import async_playwright
        
        async def crawl_async():
            crawler = HetuShuQuickCrawler(max_pages_per_category=2)  # 限制页数而不是书籍数量
            category = options.get('category', '玄幻小说')
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    # 爬取书籍信息
                    books = await crawler.crawl_category(browser, category)
                    return books
                finally:
                    await browser.close()
        
        # 运行异步爬虫
        books = asyncio.run(crawl_async())
        category = options.get('category', '玄幻小说')  # 重新获取category变量
        
        # 保存到数据库
        saved_count = 0
        for book in books:
            novel, created = Novel.objects.get_or_create(
                title=book['title'],
                defaults={
                    'author': book['author'],
                    'description': f'从{category}分类爬取',
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if created:
                # 获取或创建小说源
                source, _ = NovelSource.objects.get_or_create(
                    name='hetushu',
                    defaults={
                        'source_type': '和图书',
                        'base_url': 'https://www.hetushu.com',
                        'is_active': True,
                        'last_crawl_at': timezone.now(),
                        'crawl_count': 1
                    }
                )
                
                # 创建小说来源关联
                NovelSourceRelation.objects.get_or_create(
                    novel=novel,
                    source=source,
                    defaults={
                        'source_url': book['url'],
                        'is_primary': True,
                        'last_sync_at': timezone.now(),
                        'sync_count': 1
                    }
                )
                saved_count += 1
                
        self.stdout.write(
            self.style.SUCCESS(f'快速爬虫完成，保存了 {saved_count} 本新书')
        )

    def run_book_crawler(self, options):
        """运行详细书籍爬虫"""
        book_id = options.get('book_id')
        if not book_id:
            self.stdout.write(
                self.style.ERROR('book类型需要提供--book-id参数')
            )
            return
            
        self.stdout.write(f'启动详细爬虫，爬取书籍ID: {book_id}')
        
        crawler = HetuShuBookCrawler()
        book_data = crawler.crawl_book(book_id)
        
        if book_data:
            # 保存书籍和章节信息
            novel, created = Novel.objects.get_or_create(
                title=book_data['title'],
                defaults={
                    'author': book_data['author'],
                    'description': book_data.get('description', ''),
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            # 保存章节
            chapter_count = 0
            for chapter_data in book_data.get('chapters', []):
                chapter, created = Chapter.objects.get_or_create(
                    novel=novel,
                    title=chapter_data['title'],
                    defaults={
                        'content': chapter_data.get('content', ''),
                        'chapter_number': chapter_data.get('chapter_number', 0),
                        'created_at': timezone.now()
                    }
                )
                if created:
                    chapter_count += 1
                    
            self.stdout.write(
                self.style.SUCCESS(f'详细爬虫完成，保存了 {chapter_count} 个章节')
            )
        else:
            self.stdout.write(
                self.style.ERROR('未能获取到书籍数据')
            )

    def run_universal_crawler(self, options):
        """运行通用下载器"""
        book_id = options.get('book_id')
        if not book_id:
            self.stdout.write(
                self.style.ERROR('universal类型需要提供--book-id参数')
            )
            return
            
        self.stdout.write(f'启动通用下载器，处理书籍ID: {book_id}')
        
        downloader = UniversalNovelDownloader()
        result = downloader.download_novel(book_id)
        
        if result:
            self.stdout.write(
                self.style.SUCCESS(f'通用下载器完成，结果: {result}')
            )
        else:
            self.stdout.write(
                self.style.ERROR('通用下载器执行失败')
            )