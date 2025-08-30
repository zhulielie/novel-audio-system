from django.core.management.base import BaseCommand
from django.db import transaction
from novels.models import Novel, Chapter
import re

class Command(BaseCommand):
    help = '修复章节标题格式，将阿拉伯数字改为中文数字'

    def add_arguments(self, parser):
        parser.add_argument(
            '--novel',
            type=str,
            help='指定小说标题（可选）',
        )
        parser.add_argument(
            '--reset-ai-sorting',
            action='store_true',
            help='重置AI排序的章节序号',
        )
        parser.add_argument(
            '--populate-sort-numbers',
            action='store_true',
            help='填充章节排序数字字段',
        )
        parser.add_argument(
            '--fix-content-title-mismatch',
            action='store_true',
            help='根据内容修复标题不匹配问题',
        )

    def handle(self, *args, **options):
        # 如果是修复内容标题不匹配
        if options['fix_content_title_mismatch']:
            self.fix_content_title_mismatch_mode(options)
            return

        # 如果是填充排序数字
        if options['populate_sort_numbers']:
            self.populate_sort_numbers_mode(options)
            return

        # 如果只是重置AI排序
        if options['reset_ai_sorting']:
            self.reset_ai_sorting_mode(options)
            return

        # 正常模式：修复章节标题格式
        self.fix_title_format_mode(options)

    def reset_ai_sorting_mode(self, options):
        """重置AI排序模式"""
        # 获取要处理的章节
        if options['novel']:
            novels = Novel.objects.filter(title__icontains=options['novel'])
        else:
            novels = Novel.objects.all()

        total_reset = 0

        for novel in novels:
            self.stdout.write(f'处理小说: {novel.title}')
            reset_count = self.reset_ai_sorting(novel)
            total_reset += reset_count

        self.stdout.write(self.style.SUCCESS(f'总共重置了 {total_reset} 个AI排序的章节'))

    def fix_title_format_mode(self, options):
        """修复标题格式模式"""
        # 定义中文数字映射
        chinese_numbers = {
            1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
            6: '六', 7: '七', 8: '八', 9: '九', 10: '十',
            100: '百', 1000: '千', 10000: '万'
        }

        def number_to_chinese(num):
            if num <= 10:
                return chinese_numbers.get(num, str(num))
            elif num < 100:
                tens = num // 10
                units = num % 10
                result = chinese_numbers.get(tens, str(tens)) + '十'
                if units > 0:
                    result += chinese_numbers.get(units, str(units))
                return result
            elif num < 1000:
                hundreds = num // 100
                remainder = num % 100
                result = chinese_numbers.get(hundreds, str(hundreds)) + '百'
                if remainder > 0:
                    result += number_to_chinese(remainder)
                return result
            else:
                thousands = num // 1000
                remainder = num % 1000
                result = chinese_numbers.get(thousands, str(thousands)) + '千'
                if remainder > 0:
                    result += number_to_chinese(remainder)
                return result

        # 获取要处理的章节
        if options['novel']:
            novels = Novel.objects.filter(title__icontains=options['novel'])
        else:
            novels = Novel.objects.all()

        total_fixed = 0

        for novel in novels:
            self.stdout.write(f'处理小说: {novel.title}')

            # 查找格式错误的章节标题
            wrong_chapters = Chapter.objects.filter(
                novel=novel,
                title__regex=r'第\d+章'
            ).exclude(
                title__regex=r'第[一二三四五六七八九十百千]+章'
            )

            fixed_count = 0
            for chapter in wrong_chapters:
                original_title = chapter.title
                match = re.search(r'第(\d+)章', original_title)
                if match:
                    chapter_num = int(match.group(1))
                    new_title = f'第{number_to_chinese(chapter_num)}章'
                    chapter.title = new_title
                    chapter.save()
                    fixed_count += 1
                    self.stdout.write(f'  修复: {original_title} -> {new_title}')

            total_fixed += fixed_count
            self.stdout.write(f'  修复了 {fixed_count} 个章节标题')

        self.stdout.write(self.style.SUCCESS(f'总共修复了 {total_fixed} 个章节标题'))

    def reset_ai_sorting(self, novel):
        """重置AI排序，将偏移量序号恢复为正常序号"""
        offset = 100000
        chapters = Chapter.objects.filter(novel=novel, chapter_number__gte=offset).order_by('chapter_number')

        if chapters.exists():
            self.stdout.write(f'发现 {chapters.count()} 个AI排序的章节，需要重置')

            with transaction.atomic():
                for new_order, chapter in enumerate(chapters):
                    original_title = chapter.title
                    chapter.chapter_number = new_order + 1
                    chapter.title = original_title
                    chapter.save(update_fields=['chapter_number'])
                    self.stdout.write(f'  重置: 序号{chapter.chapter_number} <- {chapter.title}')

            return chapters.count()
        return 0

    def populate_sort_numbers_mode(self, options):
        """填充章节排序数字模式"""
        # 定义中文数字映射
        chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000
        }

        def extract_chinese_number(text):
            """从章节标题中提取数字并转换为阿拉伯数字"""
            if not text:
                return 1

            # 移除"第"和"章"
            text = text.replace('第', '').replace('章', '')

            # 如果是纯数字，直接返回
            if text.isdigit():
                return int(text)

            # 特殊处理一些常见的数字格式
            special_cases = {
                '十': 10, '一十': 10, '二十': 20, '三十': 30, '四十': 40, '五十': 50,
                '六十': 60, '七十': 70, '八十': 80, '九十': 90,
                '百': 100, '千': 1000, '万': 10000
            }

            if text in special_cases:
                return special_cases[text]

            # 使用简单的方法：将中文数字转换为对应的阿拉伯数字
            # 例如：第一章 -> 1, 第二十章 -> 20, 第一百章 -> 100
            result = 0
            current_num = 0
            i = 0

            while i < len(text):
                char = text[i]

                if char in chinese_numbers:
                    if char == '十':
                        if current_num == 0:
                            current_num = 1  # "十"表示10
                        current_num *= 10
                    elif char == '百':
                        result += current_num * 100
                        current_num = 0
                    elif char == '千':
                        result += current_num * 1000
                        current_num = 0
                    elif char == '万':
                        result += current_num * 10000
                        current_num = 0
                    else:
                        current_num += chinese_numbers[char]
                else:
                    i += 1
                    continue
                i += 1

            result += current_num
            return result if result > 0 else 1

        # 获取要处理的章节
        if options['novel']:
            novels = Novel.objects.filter(title__icontains=options['novel'])
        else:
            novels = Novel.objects.all()

        total_updated = 0

        for novel in novels:
            self.stdout.write(f'处理小说: {novel.title}')

            # 获取所有章节
            chapters = Chapter.objects.filter(novel=novel)
            updated_count = 0

            for chapter in chapters:
                sort_number = extract_chinese_number(chapter.title)
                if chapter.chapter_sort_number != sort_number:
                    chapter.chapter_sort_number = sort_number
                    chapter.save(update_fields=['chapter_sort_number'])
                    updated_count += 1
                    self.stdout.write(f'  更新: {chapter.title} -> 排序数字 {sort_number}')

            total_updated += updated_count
            self.stdout.write(f'  更新了 {updated_count} 个章节的排序数字')

        self.stdout.write(self.style.SUCCESS(f'总共更新了 {total_updated} 个章节的排序数字'))

    def fix_content_title_mismatch_mode(self, options):
        """根据内容修复标题不匹配问题"""
        import re

        # 中文数字映射
        chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000
        }

        def extract_chinese_number(text):
            if not text:
                return 1

            # 移除'第'和'章'
            text = text.replace('第', '').replace('章', '')

            # 如果是纯数字，直接返回
            if text.isdigit():
                return int(text)

            # 特殊处理一些常见的数字格式
            special_cases = {
                '十': 10, '一十': 10, '二十': 20, '三十': 30, '四十': 40, '五十': 50,
                '六十': 60, '七十': 70, '八十': 80, '九十': 90,
                '百': 100, '千': 1000, '万': 10000
            }

            if text in special_cases:
                return special_cases[text]

            # 使用简单的方法：将中文数字转换为对应的阿拉伯数字
            result = 0
            current_num = 0
            i = 0

            while i < len(text):
                char = text[i]

                if char in chinese_numbers:
                    if char == '十':
                        if current_num == 0:
                            current_num = 1  # '十'表示10
                        current_num *= 10
                    elif char == '百':
                        result += current_num * 100
                        current_num = 0
                    elif char == '千':
                        result += current_num * 1000
                        current_num = 0
                    elif char == '万':
                        result += current_num * 10000
                        current_num = 0
                    else:
                        current_num += chinese_numbers[char]
                else:
                    i += 1
                    continue
                i += 1

            result += current_num
            return result if result > 0 else 1

        def number_to_chinese(num):
            """将数字转换为中文数字格式"""
            if num <= 10:
                chinese_digits = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                return chinese_digits[num]
            elif num < 100:
                tens = num // 10
                units = num % 10
                result = chinese_numbers.get(tens, str(tens)) + '十'
                if units > 0:
                    result += chinese_numbers.get(units, str(units))
                return result
            elif num < 1000:
                hundreds = num // 100
                remainder = num % 100
                result = chinese_numbers.get(hundreds, str(hundreds)) + '百'
                if remainder > 0:
                    result += number_to_chinese(remainder)
                return result
            else:
                thousands = num // 1000
                remainder = num % 1000
                result = chinese_numbers.get(thousands, str(thousands)) + '千'
                if remainder > 0:
                    result += number_to_chinese(remainder)
                return result

        # 获取要处理的章节
        if options['novel']:
            novels = Novel.objects.filter(title__icontains=options['novel'])
        else:
            novels = Novel.objects.all()

        total_fixed = 0

        for novel in novels:
            self.stdout.write(f'处理小说: {novel.title}')

            # 获取所有章节
            chapters = Chapter.objects.filter(novel=novel)
            fixed_count = 0

            for chapter in chapters:
                content = chapter.content[:500] if chapter.content else ''  # 检查前500字符

                # 从内容中提取章节号
                content_match = re.search(r'第([一二三四五六七八九十百千]+|[0-9]+)章', content)

                if content_match:
                    content_chapter_text = content_match.group(1)
                    if content_chapter_text.isdigit():
                        content_number = int(content_chapter_text)
                    else:
                        content_number = extract_chinese_number('第' + content_chapter_text + '章')

                    # 获取当前标题的数字
                    title_number = extract_chinese_number(chapter.title)

                    # 如果内容和标题不匹配，修复标题
                    if content_number != title_number:
                        # 生成新的标题
                        new_title = f'第{number_to_chinese(content_number)}章'

                        # 更新章节标题
                        chapter.title = new_title
                        chapter.save(update_fields=['title'])

                        # 同时更新排序数字
                        chapter.chapter_sort_number = content_number
                        chapter.save(update_fields=['chapter_sort_number'])

                        fixed_count += 1
                        self.stdout.write(f'  修复: {chapter.title} (原标题数字: {title_number}) -> {new_title} (内容数字: {content_number})')

            total_fixed += fixed_count
            self.stdout.write(f'  修复了 {fixed_count} 个章节的标题和排序数字')

        self.stdout.write(self.style.SUCCESS(f'总共修复了 {total_fixed} 个章节的标题和内容匹配问题'))
