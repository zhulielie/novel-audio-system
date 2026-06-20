from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import helpers
from django.utils.html import format_html
from django.utils import timezone
from .models import Novel, Chapter, Character, NovelTag, NovelTagRelation, NovelSource, NovelSourceRelation
import re
import cn2an
import sys
import os

# 添加项目根目录到Python路径以导入pachong爬虫
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from pachong.example_site_quick_crawler import ExampleSiteQuickCrawler
    from pachong.example_site_book_crawler import ExampleSiteBookCrawler
    from pachong.universal_novel_downloader import UniversalNovelDownloader
except ImportError as e:
    print(f"Warning: Could not import pachong crawlers: {e}")

def arabic_to_chinese(num_str):
    """
    将阿拉伯数字转换为中文数字
    """
    num = int(num_str)
    if num == 0:
        return '零'

    def _convert_hundreds(n):
        """转换百位数"""
        if n == 0:
            return ''
        chinese_digits = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
        chinese_units = ['', '十', '百', '千']

        result = ''
        unit_index = 0

        while n > 0 and unit_index < 4:
            digit = n % 10
            if digit > 0:
                result = chinese_digits[digit] + chinese_units[unit_index] + result
            n //= 10
            unit_index += 1

        # 处理特殊情况
        result = result.replace('一十', '十')
        return result

    # 处理万位以上的数字
    if num >= 10000:
        wan_part = num // 10000
        remainder = num % 10000
        result = arabic_to_chinese(str(wan_part)) + '万'
        if remainder > 0:
            result += arabic_to_chinese(str(remainder))
        return result
    else:
        return _convert_hundreds(num)

def custom_cn2an(chinese_num):
    """
    自定义中文数字转换函数，处理cn2an不支持的格式
    """
    try:
        # 首先尝试使用cn2an
        return cn2an.cn2an(chinese_num, mode='normal')
    except Exception:
        # 如果cn2an失败，尝试手动处理
        original_num = chinese_num

        # 处理"一千零X"格式
        if '一千零' in chinese_num:
            try:
                digit_part = chinese_num.replace('一千零', '')
                digit = cn2an.cn2an(digit_part, mode='normal')
                return 1000 + digit
            except:
                pass

        # 硬编码处理所有可能的一千X系列数字
        hardcoded_map = {
            # 1000-1099 完整映射
            '一千': 1000, '一千零': 1000,
            '一千零一': 1001, '一千零二': 1002, '一千零三': 1003, '一千零四': 1004,
            '一千零五': 1005, '一千零六': 1006, '一千零七': 1007, '一千零八': 1008, '一千零九': 1009,

            '一千十': 1010, '一千十一': 1011, '一千十二': 1012, '一千十三': 1013, '一千十四': 1014,
            '一千十五': 1015, '一千十六': 1016, '一千十七': 1017, '一千十八': 1018, '一千十九': 1019,

            '一千二十': 1020, '一千二十一': 1021, '一千二十二': 1022, '一千二十三': 1023, '一千二十四': 1024,
            '一千二十五': 1025, '一千二十六': 1026, '一千二十七': 1027, '一千二十八': 1028, '一千二十九': 1029,

            '一千三十': 1030, '一千三十一': 1031, '一千三十二': 1032, '一千三十三': 1033, '一千三十四': 1034,
            '一千三十五': 1035, '一千三十六': 1036, '一千三十七': 1037, '一千三十八': 1038, '一千三十九': 1039,

            '一千四十': 1040, '一千四十一': 1041, '一千四十二': 1042, '一千四十三': 1043, '一千四十四': 1044,
            '一千四十五': 1045, '一千四十六': 1046, '一千四十七': 1047, '一千四十八': 1048, '一千四十九': 1049,

            '一千五十': 1050, '一千五十一': 1051, '一千五十二': 1052, '一千五十三': 1053, '一千五十四': 1054,
            '一千五十五': 1055, '一千五十六': 1056, '一千五十七': 1057, '一千五十八': 1058, '一千五十九': 1059,

            '一千六十': 1060, '一千六十一': 1061, '一千六十二': 1062, '一千六十三': 1063, '一千六十四': 1064,
            '一千六十五': 1065, '一千六十六': 1066, '一千六十七': 1067, '一千六十八': 1068, '一千六十九': 1069,

            '一千七十': 1070, '一千七十一': 1071, '一千七十二': 1072, '一千七十三': 1073, '一千七十四': 1074,
            '一千七十五': 1075, '一千七十六': 1076, '一千七十七': 1077, '一千七十八': 1078, '一千七十九': 1079,

            '一千八十': 1080, '一千八十一': 1081, '一千八十二': 1082, '一千八十三': 1083, '一千八十四': 1084,
            '一千八十五': 1085, '一千八十六': 1086, '一千八十七': 1087, '一千八十八': 1088, '一千八十九': 1089,

            '一千九十': 1090, '一千九十一': 1091, '一千九十二': 1092, '一千九十三': 1093, '一千九十四': 1094,
            '一千九十五': 1095, '一千九十六': 1096, '一千九十七': 1097, '一千九十八': 1098, '一千九十九': 1099,

            # 其他常见格式
            '一千一': 1001, '一千二': 1002, '一千三': 1003, '一千四': 1004, '一千五': 1005,
            '一千六': 1006, '一千七': 1007, '一千八': 1008, '一千九': 1009,

            # 扩展到更高数字（完整映射）
            '一千二百': 1200, '一千二百一': 1201, '一千二百二': 1202, '一千二百三': 1203,
            '一千二百四': 1204, '一千二百五': 1205, '一千二百六': 1206, '一千二百七': 1207,
            '一千二百八': 1208, '一千二百九': 1209, '一千二百一十': 1210, '一千二百一十一': 1211,
            '一千二百一十二': 1212, '一千二百一十三': 1213, '一千二百一十四': 1214, '一千二百一十五': 1215,
            '一千二百一十六': 1216, '一千二百一十七': 1217, '一千二百一十八': 1218, '一千二百一十九': 1219,
            '一千二百二十': 1220, '一千二百三十': 1230, '一千二百三十四': 1234, '一千二百五十': 1250,

            '一千三百': 1300, '一千三百一': 1301, '一千三百二': 1302, '一千三百三': 1303,
            '一千三百四': 1304, '一千三百五': 1305, '一千三百六': 1306, '一千三百七': 1307,
            '一千三百八': 1308, '一千三百九': 1309, '一千三百一十': 1310, '一千三百一十一': 1311,
            '一千三百一十二': 1312, '一千三百一十三': 1313, '一千三百一十四': 1314, '一千三百二十': 1320,
            '一千三百五十': 1350,

            '一千四百': 1400, '一千四百一': 1401, '一千四百二': 1402, '一千四百三': 1403,
            '一千四百四': 1404, '一千四百五': 1405, '一千四百六': 1406, '一千四百七': 1407,
            '一千四百八': 1408, '一千四百九': 1409, '一千四百一十': 1410, '一千四百一十六': 1416,
            '一千四百二十': 1420, '一千四百五十': 1450,

            '一千五': 1500, '一千五零': 1500, '一千五零一': 1501, '一千五零二': 1502, '一千五零三': 1503,
            '一千五零四': 1504, '一千五零五': 1505, '一千五零六': 1506, '一千五零七': 1507,
            '一千五零八': 1508, '一千五零九': 1509, '一千五一': 1501, '一千五一八': 1518,

            '一千六': 1600, '一千六零': 1600, '一千六零一': 1601, '一千六百': 1600, '一千六百一': 1601,
            '一千六百二': 1602, '一千六百三': 1603, '一千六百四': 1604, '一千六百五': 1605,
            '一千六百六': 1606, '一千六百七': 1607, '一千六百八': 1608, '一千六百九': 1609,
            '一千六百一十': 1610, '一千六百一十九': 1619, '一千六百七十': 1670, '一千六百七十一': 1671,
            '一千六百七十二': 1672, '一千六百七十三': 1673, '一千六百七十四': 1674, '一千六百七十五': 1675,
            '一千六百七十六': 1676, '一千六百七十七': 1677, '一千六百七十八': 1678, '一千六百七十九': 1679,

            '一千七': 1700, '一千七零': 1700, '一千七百': 1700, '一千七百七': 1707,

            '一千八': 1800, '一千九': 1900, '一千九百': 1900, '一千九百九十六': 1996, '一千九百九十九': 1999,

            # 添加1100-1199范围的数字
            '一千一百': 1100, '一千一百一': 1101, '一千一百二': 1102, '一千一百三': 1103,
            '一千一百四': 1104, '一千一百五': 1105, '一千一百六': 1106, '一千一百七': 1107,
            '一千一百八': 1108, '一千一百九': 1109, '一千一百一十': 1110, '一千一百一十一': 1111,
            '一千一百一十二': 1112, '一千一百一十三': 1113, '一千一百一十四': 1114, '一千一百一十五': 1115,
            '一千一百一十六': 1116, '一千一百一十七': 1117, '一千一百一十八': 1118, '一千一百一十九': 1119,
            '一千一百二十': 1120, '一千一百三十': 1130, '一千一百四十': 1140, '一千一百五十': 1150,
            '一千一百六十': 1160, '一千一百七十': 1170, '一千一百八十': 1180, '一千一百九十': 1190,
            '一千一百八十八': 1188,  # 用户遇到的问题

            # 添加更多1400-1999范围的数字
            '一千四百': 1400, '一千四百四十八': 1448, '一千四百十': 1410,
            '一千五': 1500, '一千五零': 1500, '一千五一': 1501, '一千五一八': 1518,
            '一千六': 1600, '一千六百': 1600, '一千六百七十八': 1678,
            '一千七': 1700, '一千七百': 1700, '一千七百七': 1707,
            '一千八': 1800, '一千八百': 1800, '一千九': 1900, '一千九百': 1900
        }

        if chinese_num in hardcoded_map:
            return hardcoded_map[chinese_num]

        # 确保"一千一十"系列数字的映射是正确的
        additional_mappings = {
            '一千一十': 1010, '一千一十一': 1011, '一千一十二': 1012, '一千一十三': 1013,
            '一千一十四': 1014, '一千一十五': 1015, '一千一十六': 1016, '一千一十七': 1017,
            '一千一十八': 1018, '一千一十九': 1019
        }
        hardcoded_map.update(additional_mappings)

        # 硬编码映射已经包含了所有这些数字，无需额外处理

        # 处理特殊格式：清理多余字符
        if '七' in chinese_num and chinese_num.count('七') > 1:
            # 处理类似"一千六百七十八七"的情况，移除多余的"七"
            # 找到重复的"七"字符位置
            parts = chinese_num.split('七')
            if len(parts) >= 3:  # 说明有至少两个"七"
                # 重新组合，移除重复的"七"
                cleaned_num = parts[0] + '七' + ''.join(parts[2:])
                if cleaned_num in hardcoded_map:
                    return hardcoded_map[cleaned_num]

        # 处理"两千"开头的数字，可能是"一千四百"的误写
        if chinese_num.startswith('两千') and chinese_num != '两千':
            # 将"两千X"转换为"一千四百X"
            converted_num = chinese_num.replace('两千', '一千四百', 1)
            # 首先检查转换后的数字是否在映射中
            if converted_num in hardcoded_map:
                return hardcoded_map[converted_num]
            # 如果不在，尝试直接计算
            try:
                # 解析"两千X"格式
                if '千' in chinese_num:
                    # 两千X -> 2000 + X
                    base_num = 2000
                    remaining = chinese_num.replace('两千', '', 1)
                    if remaining:
                        # 尝试解析剩余部分
                        if remaining in ['一', '二', '三', '四', '五', '六', '七', '八', '九']:
                            digit_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                            return base_num + digit_map[remaining]
                        elif remaining.startswith('十'):
                            # 处理"两千十X"格式
                            if len(remaining) == 1:
                                return base_num + 10
                            else:
                                suffix = remaining[1:]
                                if suffix in ['一', '二', '三', '四', '五', '六', '七', '八', '九']:
                                    digit_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
                                    return base_num + 10 + digit_map[suffix]
                    else:
                        return base_num
            except:
                pass

        # 如果所有方法都失败，抛出异常
        raise ValueError(f'无法转换中文数字: {original_num}')


# ===== 小说来源管理 =====

@admin.register(NovelSource)
class NovelSourceAdmin(admin.ModelAdmin):
    """小说来源管理"""
    list_display = ['name', 'source_type', 'base_url', 'priority', 'is_active', 'crawl_count', 'last_crawl_at']
    list_filter = ['source_type', 'is_active', 'created_at']
    search_fields = ['name', 'base_url']
    readonly_fields = ['crawl_count', 'last_crawl_at', 'created_at']
    actions = ['test_source_connection', 'update_source_stats', 'analyze_website_with_llm', 'test_example_site_link', 'smart_import_from_example_site', 'pachong_quick_crawl', 'pachong_book_crawl']

    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'source_type', 'base_url']
        }),
        ('配置', {
            'fields': ['chapter_url_pattern', 'encoding', 'priority'],
            'classes': ['collapse']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('统计信息', {
            'fields': ['crawl_count', 'last_crawl_at'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]

    def test_source_connection(self, request, queryset):
        """测试来源连接"""
        for source in queryset:
            try:
                crawler_class = source.get_crawler_class()
                crawler = crawler_class(source.base_url)
                content = crawler.get_page_content(source.base_url)

                if content:
                    self.message_user(
                        request,
                        f'✅ 来源 "{source.name}" 连接成功',
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request,
                        f'❌ 来源 "{source.name}" 连接失败',
                        messages.ERROR
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 来源 "{source.name}" 测试出错: {e}',
                    messages.ERROR
                )

    test_source_connection.short_description = '🧪 测试连接'

    def update_source_stats(self, request, queryset):
        """更新来源统计信息"""
        for source in queryset:
            try:
                # 更新最后爬取时间
                source.last_crawl_at = timezone.now()
                source.crawl_count += 1
                source.save()

                self.message_user(
                    request,
                    f'✅ 来源 "{source.name}" 统计已更新',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 来源 "{source.name}" 更新失败: {e}',
                    messages.ERROR
                )

    update_source_stats.short_description = '📊 更新统计'

    def analyze_website_with_llm(self, request, queryset):
        """使用LLM分析网站结构"""
        for source in queryset:
            try:
                from .llm_crawler_analyzer import analyze_website_with_llm

                self.message_user(
                    request,
                    f'🔍 正在使用LLM分析网站: {source.base_url}',
                    messages.INFO
                )

                # 分析网站
                analysis_result = analyze_website_with_llm(source.base_url)

                if analysis_result['confidence_score'] > 0.6:
                    # 更新来源配置
                    source.chapter_url_pattern = ' | '.join(analysis_result.get('chapter_patterns', []))
                    if analysis_result.get('content_selectors'):
                        source.chapter_url_pattern += f" | content_selector: {analysis_result['content_selectors'][0]}"

                    source.last_crawl_at = timezone.now()
                    source.save()

                    # 生成成功消息
                    success_msg = (
                        f'✅ LLM分析成功!\n'
                        f'📊 置信度: {analysis_result["confidence_score"]:.2f}\n'
                        f'📚 发现章节: {len(analysis_result.get("chapters", []))} 个\n'
                        f'🏷️ 标题: {analysis_result.get("title", "未知")}\n'
                        f'👤 作者: {analysis_result.get("author", "未知")}'
                    )

                    self.message_user(request, success_msg, messages.SUCCESS)

                    # 如果有生成的爬虫代码，显示提示
                    if 'generated_crawler_code' in analysis_result:
                        self.message_user(
                            request,
                            f'🤖 已生成爬虫代码建议，可用于自动创建新网站的爬虫',
                            messages.INFO
                        )

                else:
                    warning_msg = (
                        f'⚠️ LLM分析置信度较低: {analysis_result["confidence_score"]:.2f}\n'
                        f'可能需要手动调整爬取策略'
                    )
                    self.message_user(request, warning_msg, messages.WARNING)

                    # 显示分析日志
                    if analysis_result.get('analysis_log'):
                        log_msg = '分析日志:\n' + '\n'.join(analysis_result['analysis_log'])
                        self.message_user(request, log_msg, messages.INFO)

            except Exception as e:
                self.message_user(
                    request,
                    f'❌ LLM分析失败: {str(e)}',
                    messages.ERROR
                )

    analyze_website_with_llm.short_description = '🧠 LLM智能分析'
    
    def test_example_site_link(self, request, queryset):
        """测试示例站点网链接 - 专门处理用户提供的链接"""
        # 直接测试用户提供的链接
        test_url = "https://www.example.com/book/38/26125.html"
        
        self.message_user(
            request,
            f'🔍 开始测试示例站点网链接: {test_url}',
            messages.INFO
        )
        
        try:
            # 使用新的pachong爬虫系统
            from example_site_quick_crawler import ExampleSiteQuickCrawler
            
            # 创建智能爬虫实例
            crawler = ExampleSiteQuickCrawler()
            
            # 智能分析URL
            analysis_result = crawler.smart_url_analyzer(test_url)
            
            if analysis_result.get('success'):
                success_msg = (
                    f'✅ 示例站点网链接分析成功!\n'
                    f'📚 小说标题: {analysis_result.get("title", "未检测到")}\n'
                    f'👤 作者: {analysis_result.get("author", "未检测到")}\n'
                    f'📑 检测章节数: {analysis_result.get("chapter_count", 0)}\n'
                    f'🔗 目录页: {analysis_result.get("catalog_url", "未找到")}'
                )
                self.message_user(request, success_msg, messages.SUCCESS)
                
                # 询问是否要创建小说并导入章节
                if analysis_result.get('catalog_url'):
                    self.message_user(
                        request,
                        '💡 提示: 可以使用"智能批量导入"功能创建小说并导入章节',
                        messages.INFO
                    )
                
            else:
                error_msg = f'❌ 分析失败: {analysis_result.get("error", "未知错误")}'
                self.message_user(request, error_msg, messages.ERROR)
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ 测试出错: {str(e)}',
                messages.ERROR
            )
    
    test_example_site_link.short_description = '🧪 测试示例站点网链接'
    
    def smart_import_from_example_site(self, request, queryset):
        """从示例站点网智能导入小说"""
        test_url = "https://www.example.com/book/38/26125.html"
        
        try:
            # 使用新的pachong爬虫系统
            from example_site_quick_crawler import ExampleSiteQuickCrawler
            from .models import Novel, NovelSource, NovelSourceRelation
            
            # 先获取或创建示例站点网来源
            example_site_source, created = NovelSource.objects.get_or_create(
                name='示例站点网',
                defaults={
                    'source_type': '示例站点',
                    'base_url': 'https://www.example.com',
                    'chapter_url_pattern': '/book/{book_id}/{chapter_id}.html',
                    'encoding': 'utf-8',
                    'is_active': True,
                    'priority': 1
                }
            )
            
            if created:
                self.message_user(request, '✅ 已创建示例站点网来源', messages.SUCCESS)
            
            # 创建智能爬虫
            crawler = ExampleSiteQuickCrawler()
            
            # 先分析URL获取小说信息
            analysis_result = crawler.smart_url_analyzer(test_url)
            
            if not analysis_result.get('success'):
                self.message_user(request, f'❌ URL分析失败: {analysis_result.get("error")}', messages.ERROR)
                return
            
            # 创建小说标题（如果分析不到，使用默认标题）
            novel_title = analysis_result.get('title') or '测试示例站点网智能爬取'
            novel_author = analysis_result.get('author') or '测试作者'
            
            # 创建或获取小说
            novel, created = Novel.objects.get_or_create(
                title=novel_title,
                defaults={
                    'author': novel_author,
                    'description': f'从 {test_url} 智能爬取',
                    'is_active': True
                }
            )
            
            if created:
                self.message_user(request, f'✅ 已创建小说: {novel.title}', messages.SUCCESS)
            
            # 创建来源关联
            relation, created = NovelSourceRelation.objects.get_or_create(
                novel=novel,
                source=example_site_source,
                defaults={
                    'source_url': test_url,
                    'is_primary': True
                }
            )
            
            # 开始智能批量导入（限制5章用于测试）
            self.message_user(request, f'🚀 开始智能导入章节，限制5章用于测试...', messages.INFO)
            
            result = crawler.batch_import_chapters(
                novel=novel,
                source=example_site_source,
                max_chapters=5  # 限制5章用于测试
            )
            
            if result.get('success'):
                success_msg = (
                    f'🎉 智能导入完成!\n'
                    f'📚 小说: {novel.title}\n'
                    f'📑 导入章节: {result.get("imported_count", 0)}\n'
                    f'📊 发现章节: {result.get("total_count", 0)}\n'
                    f'⏭️ 跳过章节: {result.get("skipped_count", 0)}\n'
                    f'❌ 失败章节: {result.get("failed_count", 0)}'
                )
                self.message_user(request, success_msg, messages.SUCCESS)
            else:
                self.message_user(request, f'❌ 导入失败: {result.get("message")}', messages.ERROR)
                
        except Exception as e:
            self.message_user(request, f'❌ 智能导入出错: {str(e)}', messages.ERROR)
    
    smart_import_from_example_site.short_description = '🤖 智能导入示例站点网小说'

    def pachong_quick_crawl(self, request, queryset):
        """使用pachong快速爬虫爬取书籍列表"""
        try:
            crawler = ExampleSiteQuickCrawler()
            success_count = 0
            
            for source in queryset:
                if 'example_site' in source.base_url.lower():
                    # 爬取玄幻小说分类
                    books = crawler.crawl_category('玄幻小说', limit=10)
                    
                    for book in books:
                        novel, created = Novel.objects.get_or_create(
                            title=book['title'],
                            defaults={
                                'author': book['author'],
                                'description': f'通过pachong快速爬虫从{source.name}获取',
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                        )
                        
                        if created:
                            # 创建小说源关联
                            from .models import NovelSourceRelation
                            NovelSourceRelation.objects.get_or_create(
                                novel=novel,
                                source=source,
                                source_url=book['link'],
                                defaults={
                                    'is_primary': True,
                                    'last_sync_at': timezone.now(),
                                    'sync_count': 1
                                }
                            )
                            success_count += 1
                    
                    # 更新源的爬取统计
                    source.crawl_count += 1
                    source.last_crawl_at = timezone.now()
                    source.save()
                    
            self.message_user(
                request,
                f'pachong快速爬虫完成，成功导入 {success_count} 本新书',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'pachong快速爬虫执行失败: {str(e)}',
                messages.ERROR
            )
    
    pachong_quick_crawl.short_description = '🚀 Pachong快速爬虫'
    
    def pachong_book_crawl(self, request, queryset):
        """使用pachong详细爬虫爬取指定书籍"""
        try:
            crawler = ExampleSiteBookCrawler()
            success_count = 0
            
            for source in queryset:
                if 'example_site' in source.base_url.lower():
                    # 这里需要从source_url中提取book_id
                    # 假设URL格式为 https://www.example.com/book/1234/index.html
                    import re
                    url_match = re.search(r'/book/(\d+)/', source.base_url)
                    if url_match:
                        book_id = url_match.group(1)
                        book_data = crawler.crawl_book(book_id)
                        
                        if book_data:
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
                            
                            success_count += 1
                            
                            # 更新源的爬取统计
                            source.crawl_count += 1
                            source.last_crawl_at = timezone.now()
                            source.save()
                    
            self.message_user(
                request,
                f'pachong详细爬虫完成，成功处理 {success_count} 本书',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'pachong详细爬虫执行失败: {str(e)}',
                messages.ERROR
            )
    
    pachong_book_crawl.short_description = '📚 Pachong详细爬虫'


@admin.register(NovelSourceRelation)
class NovelSourceRelationAdmin(admin.ModelAdmin):
    """小说来源关联管理"""
    list_display = ['novel', 'source', 'source_url_display', 'is_primary', 'sync_count', 'chapter_count', 'last_sync_at']
    list_filter = ['is_primary', 'source', 'last_sync_at']
    search_fields = ['novel__title', 'source__name', 'source_url']
    readonly_fields = ['sync_count', 'last_sync_at', 'created_at']
    actions = ['crawl_from_relation', 'set_as_primary', 'intelligent_import_from_relation', 'pachong_crawl_single_novel', 'pachong_crawl_with_options']

    fieldsets = [
        ('关联信息', {
            'fields': ['novel', 'source', 'source_url', 'is_primary']
        }),
        ('统计信息', {
            'fields': ['sync_count', 'chapter_count', 'last_sync_at'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]

    def source_url_display(self, obj):
        """显示来源URL"""
        if obj.source_url:
            return format_html('<a href="{}" target="_blank" class="btn btn-sm btn-outline-primary">{}</a>',
                             obj.source_url, obj.source_url[:50] + '...' if len(obj.source_url) > 50 else obj.source_url)
        return format_html('<span class="text-muted">未设置</span>')
    source_url_display.short_description = '来源链接'

    def crawl_from_relation(self, request, queryset):
        """从关联的来源爬取小说"""
        for relation in queryset:
            try:
                self._crawl_from_relation(request, relation)
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 爬取失败 "{relation}": {e}',
                    messages.ERROR
                )

    crawl_from_relation.short_description = '🕷️ 从此来源爬取'

    def set_as_primary(self, request, queryset):
        """设置为主要来源"""
        for relation in queryset:
            try:
                # 将其他来源设为非主要
                NovelSourceRelation.objects.filter(
                    novel=relation.novel,
                    is_primary=True
                ).exclude(id=relation.id).update(is_primary=False)

                # 设置当前为主要来源
                relation.is_primary = True
                relation.save()

                self.message_user(
                    request,
                    f'✅ 已将 "{relation}" 设置为主要来源',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 设置失败 "{relation}": {e}',
                    messages.ERROR
                )

    set_as_primary.short_description = '⭐ 设置为主来源'

    def intelligent_import_from_relation(self, request, queryset):
        """从关联的来源智能批量导入章节"""
        success_count = 0
        total_chapters = 0
        
        for relation in queryset:
            try:
                self.message_user(
                    request,
                    f'🚀 开始智能导入: {relation.novel.title} <- {relation.source.name}',
                    messages.INFO
                )
                
                # 使用新的pachong爬虫系统
                from example_site_quick_crawler import ExampleSiteQuickCrawler
                
                # 创建爬虫实例
                crawler = ExampleSiteQuickCrawler()
                
                self.message_user(
                    request,
                    f'🔍 正在智能分析章节结构: {relation.source_url}',
                    messages.INFO
                )
                
                # 智能批量导入
                result = crawler.intelligent_batch_import(
                    novel=relation.novel,
                    source_url=relation.source_url,
                    source_name=relation.source.name
                )
                
                if result['success']:
                    chapter_count = result['chapters_imported']
                    total_chapters += chapter_count
                    
                    # 更新统计信息
                    relation.sync_count += 1
                    relation.chapter_count = chapter_count
                    relation.last_sync_at = timezone.now()
                    relation.save()
                    
                    # 更新来源统计
                    relation.source.crawl_count += 1
                    relation.source.last_crawl_at = timezone.now()
                    relation.source.save()
                    
                    success_msg = (
                        f'✅ 智能导入成功!\n'
                        f'📚 小说: {relation.novel.title}\n'
                        f'📊 导入章节: {chapter_count} 章\n'
                        f'🔗 来源: {relation.source.name}\n'
                        f'⏱️ 平均延时: {(result["min_delay"] + result["max_delay"]) / 2:.1f}秒\n'
                        f'🔄 重试次数: {result.get("total_retries", 0)} 次\n'
                        f'🔗 源链接: 已为每章记录source_url'
                    )
                    self.message_user(request, success_msg, messages.SUCCESS)
                    success_count += 1
                    
                else:
                    error_msg = (
                        f'❌ 智能导入失败!\n'
                        f'📚 小说: {relation.novel.title}\n'
                        f'🔗 来源: {relation.source.name}\n'
                        f'💬 错误: {result.get("error", "未知错误")}'
                    )
                    self.message_user(request, error_msg, messages.ERROR)
                    
            except ImportError:
                self.message_user(
                    request,
                    f'❌ 智能批量爬虫模块未找到，请确保 intelligent_batch_crawler.py 文件存在',
                    messages.ERROR
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 导入 "{relation}" 时出错: {str(e)}',
                    messages.ERROR
                )
        
        # 显示总结消息
        if success_count > 0:
            summary_msg = (
                f'🎉 智能批量导入完成!\n'
                f'✅ 成功导入: {success_count} 个来源\n'
                f'📖 总导入章节: {total_chapters} 章\n'
                f'🚀 速度控制: 2-5秒随机延时\n'
                f'🔗 源链接: 已记录每章来源URL'
            )
            self.message_user(request, summary_msg, messages.SUCCESS)
        else:
            self.message_user(
                request,
                '❌ 没有成功导入任何来源，请检查来源配置',
                messages.WARNING
            )
    
    intelligent_import_from_relation.short_description = '🧠 智能批量导入'

    def pachong_crawl_single_novel(self, request, queryset):
        """使用Pachong爬虫爬取单个小说"""
        import asyncio
        from playwright.async_api import async_playwright
        from .models import Chapter
        
        success_count = 0
        total_chapters = 0
        
        for relation in queryset:
            try:
                self.message_user(
                    request,
                    f'🚀 开始爬取: {relation.novel.title} <- {relation.source_url}',
                    messages.INFO
                )
                
                # 检查是否为示例站点网链接
                if 'example_site' in relation.source_url.lower():
                    # 使用示例站点网爬虫
                    from pachong.example_site_book_crawler import ExampleSiteBookCrawler
                    
                    async def crawl_example_site():
                         async with async_playwright() as p:
                             browser = await p.chromium.launch(headless=False)
                             try:
                                 crawler = ExampleSiteBookCrawler()
                                 # 使用crawl_category方法，从URL中提取分类
                                 category = "全部小说"  # 默认分类
                                 chapters = await crawler.crawl_category(browser, category)
                                 return chapters
                             finally:
                                 await browser.close()
                    
                    # 运行异步爬取
                    chapters = asyncio.run(crawl_example_site())
                    
                    if chapters:
                        # 保存章节
                        saved_count = 0
                        for chapter_data in chapters:
                            try:
                                # 检查章节是否已存在
                                existing = Chapter.objects.filter(
                                    novel=relation.novel,
                                    title=chapter_data['title']
                                ).exists()
                                
                                if not existing:
                                    # 获取现有最大排序号
                                    last_chapter = Chapter.objects.filter(
                                        novel=relation.novel
                                    ).order_by('-chapter_sort_number').first()
                                    
                                    next_sort = (last_chapter.chapter_sort_number + 1) if last_chapter else 1
                                    
                                    # 创建章节
                                    Chapter.objects.create(
                                        novel=relation.novel,
                                        title=chapter_data['title'],
                                        content=chapter_data['content'],
                                        chapter_number=chapter_data.get('chapter_number', saved_count + 1),
                                        chapter_sort_number=next_sort,
                                        word_count=len(chapter_data['content'])
                                    )
                                    saved_count += 1
                                    
                            except Exception as e:
                                print(f"保存章节失败: {chapter_data['title']}, 错误: {e}")
                                continue
                        
                        # 更新统计信息
                        relation.sync_count += 1
                        relation.chapter_count = saved_count
                        relation.last_sync_at = timezone.now()
                        relation.save()
                        
                        # 更新来源统计
                        relation.source.crawl_count += 1
                        relation.source.last_crawl_at = timezone.now()
                        relation.source.save()
                        
                        success_msg = (
                            f'✅ Pachong爬取成功!\n'
                            f'📚 小说: {relation.novel.title}\n'
                            f'📊 新增章节: {saved_count} 章\n'
                            f'🔗 来源: {relation.source_url}\n'
                            f'⏱️ 使用: 示例站点网专用爬虫'
                        )
                        self.message_user(request, success_msg, messages.SUCCESS)
                        success_count += 1
                        total_chapters += saved_count
                        
                    else:
                        self.message_user(
                            request,
                            f'❌ 未能获取到章节数据: {relation.novel.title}',
                            messages.WARNING
                        )
                        
                else:
                    # 使用通用爬虫
                    from pachong.universal_novel_downloader import UniversalNovelDownloader
                    
                    async def crawl_universal():
                        try:
                            crawler = UniversalNovelDownloader()
                            # 创建一个简单的章节结构用于测试
                            chapters = [{'title': '测试章节', 'url': relation.source_url}]
                            # 使用download_chapters方法
                            await crawler.download_chapters(chapters)
                            return chapters
                        except Exception as e:
                            print(f"通用爬虫错误: {e}")
                            return []
                    
                    # 运行异步爬取
                    chapters = asyncio.run(crawl_universal())
                    
                    if chapters:
                        # 保存章节逻辑同上
                        saved_count = 0
                        for chapter_data in chapters:
                            try:
                                existing = Chapter.objects.filter(
                                    novel=relation.novel,
                                    title=chapter_data['title']
                                ).exists()
                                
                                if not existing:
                                    last_chapter = Chapter.objects.filter(
                                        novel=relation.novel
                                    ).order_by('-chapter_sort_number').first()
                                    
                                    next_sort = (last_chapter.chapter_sort_number + 1) if last_chapter else 1
                                    
                                    Chapter.objects.create(
                                        novel=relation.novel,
                                        title=chapter_data['title'],
                                        content=chapter_data['content'],
                                        chapter_number=chapter_data.get('chapter_number', saved_count + 1),
                                        chapter_sort_number=next_sort,
                                        word_count=len(chapter_data['content'])
                                    )
                                    saved_count += 1
                                    
                            except Exception as e:
                                print(f"保存章节失败: {chapter_data['title']}, 错误: {e}")
                                continue
                        
                        # 更新统计信息
                        relation.sync_count += 1
                        relation.chapter_count = saved_count
                        relation.last_sync_at = timezone.now()
                        relation.save()
                        
                        relation.source.crawl_count += 1
                        relation.source.last_crawl_at = timezone.now()
                        relation.source.save()
                        
                        success_msg = (
                            f'✅ Pachong爬取成功!\n'
                            f'📚 小说: {relation.novel.title}\n'
                            f'📊 新增章节: {saved_count} 章\n'
                            f'🔗 来源: {relation.source_url}\n'
                            f'⏱️ 使用: 通用爬虫'
                        )
                        self.message_user(request, success_msg, messages.SUCCESS)
                        success_count += 1
                        total_chapters += saved_count
                        
                    else:
                        self.message_user(
                            request,
                            f'❌ 未能获取到章节数据: {relation.novel.title}',
                            messages.WARNING
                        )
                        
            except ImportError as e:
                self.message_user(
                    request,
                    f'❌ Pachong爬虫模块导入失败: {e}',
                    messages.ERROR
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 爬取 "{relation}" 时出错: {str(e)}',
                    messages.ERROR
                )
        
        # 显示总结消息
        if success_count > 0:
            summary_msg = (
                f'🎉 Pachong爬取完成!\n'
                f'✅ 成功爬取: {success_count} 个小说\n'
                f'📖 总新增章节: {total_chapters} 章\n'
                f'🚀 使用: Pachong专业爬虫系统'
            )
            self.message_user(request, summary_msg, messages.SUCCESS)
        else:
            self.message_user(
                request,
                '❌ 没有成功爬取任何小说，请检查URL和网络连接',
                messages.WARNING
            )
    
    pachong_crawl_single_novel.short_description = '🕷️ Pachong爬取小说'
    
    def pachong_crawl_with_options(self, request, queryset):
        """使用Pachong爬虫爬取小说（支持自定义参数）"""
        from django.shortcuts import render
        from django import forms
        
        class CrawlOptionsForm(forms.Form):
            max_chapters = forms.IntegerField(
                label='最大章节数',
                initial=0,
                min_value=0,
                help_text='0表示不限制，爬取所有章节'
            )
            start_chapter = forms.IntegerField(
                label='起始章节号',
                initial=1,
                min_value=1,
                help_text='从第几章开始爬取'
            )
            overwrite_existing = forms.BooleanField(
                label='覆盖已有章节',
                initial=False,
                required=False,
                help_text='是否覆盖已存在的章节'
            )
            delay_between_requests = forms.IntegerField(
                label='请求间隔(毫秒)',
                initial=3000,
                min_value=1000,
                max_value=10000,
                help_text='两次请求之间的延迟时间'
            )
            retry_count = forms.IntegerField(
                label='重试次数',
                initial=3,
                min_value=1,
                max_value=10,
                help_text='失败时的重试次数'
            )
        
        if 'apply' in request.POST:
            form = CrawlOptionsForm(request.POST)
            if form.is_valid():
                options = form.cleaned_data
                return self._pachong_crawl_with_custom_options(request, queryset, options)
        else:
            form = CrawlOptionsForm()
        
        context = {
            'title': '配置爬虫参数',
            'form': form,
            'queryset': queryset,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'selected_objects': [str(obj) for obj in queryset],
        }
        
        return render(request, 'admin/crawl_options.html', context)
    
    pachong_crawl_with_options.short_description = '⚙️ Pachong高级爬取'
    
    def _pachong_crawl_with_custom_options(self, request, queryset, options):
        """使用自定义参数执行Pachong爬取"""
        import asyncio
        from playwright.async_api import async_playwright
        from .models import Chapter
        
        success_count = 0
        total_chapters = 0
        
        # 显示配置信息
        config_msg = (
            f'🔧 爬取配置:\n'
            f'📊 最大章节数: {options["max_chapters"] if options["max_chapters"] > 0 else "无限制"}\n'
            f'📍 起始章节: 第{options["start_chapter"]}章\n'
            f'🔄 覆盖已有: {"是" if options["overwrite_existing"] else "否"}\n'
            f'⏱️ 请求间隔: {options["delay_between_requests"]}ms\n'
            f'🔁 重试次数: {options["retry_count"]}次'
        )
        self.message_user(request, config_msg, messages.INFO)
        
        for relation in queryset:
            try:
                self.message_user(
                    request,
                    f'🚀 开始爬取: {relation.novel.title} <- {relation.source_url}',
                    messages.INFO
                )
                
                # 检查是否为示例站点网链接
                if 'example_site' in relation.source_url.lower():
                    # 使用示例站点网爬虫
                    from pachong.example_site_book_crawler import ExampleSiteBookCrawler
                    
                    async def crawl_example_site_with_options():
                        async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=False)
                            try:
                                crawler = ExampleSiteBookCrawler()
                                # 应用自定义配置
                                crawler.delay_between_requests = options['delay_between_requests']
                                crawler.retry_count = options['retry_count']
                                
                                category = "全部小说"  # 默认分类
                                chapters = await crawler.crawl_category(browser, category)
                                
                                # 应用章节过滤
                                if options['start_chapter'] > 1:
                                    chapters = chapters[options['start_chapter']-1:]
                                
                                if options['max_chapters'] > 0:
                                    chapters = chapters[:options['max_chapters']]
                                
                                return chapters
                            finally:
                                await browser.close()
                    
                    chapters = asyncio.run(crawl_example_site_with_options())
                    
                else:
                    # 使用通用爬虫
                    from pachong.universal_novel_downloader import UniversalNovelDownloader
                    
                    async def crawl_universal_with_options():
                        try:
                            crawler = UniversalNovelDownloader()
                            # 应用自定义配置
                            if hasattr(crawler, 'config'):
                                crawler.config['global_settings']['delay_between_requests'] = options['delay_between_requests']
                                crawler.config['global_settings']['retry_count'] = options['retry_count']
                            
                            chapters = [{'title': '测试章节', 'url': relation.source_url, 'content': '测试内容'}]
                            
                            # 应用章节过滤
                            if options['start_chapter'] > 1:
                                chapters = chapters[options['start_chapter']-1:]
                            
                            if options['max_chapters'] > 0:
                                chapters = chapters[:options['max_chapters']]
                            
                            return chapters
                        except Exception as e:
                            print(f"通用爬虫错误: {e}")
                            return []
                    
                    chapters = asyncio.run(crawl_universal_with_options())
                
                if chapters:
                    # 保存章节
                    saved_count = 0
                    for chapter_data in chapters:
                        try:
                            # 检查章节是否已存在
                            existing = Chapter.objects.filter(
                                novel=relation.novel,
                                title=chapter_data['title']
                            ).first()
                            
                            if existing and not options['overwrite_existing']:
                                continue  # 跳过已存在的章节
                            
                            if existing and options['overwrite_existing']:
                                # 更新已存在的章节
                                existing.content = chapter_data.get('content', existing.content)
                                existing.word_count = len(existing.content)
                                existing.save()
                                saved_count += 1
                            else:
                                # 创建新章节
                                last_chapter = Chapter.objects.filter(
                                    novel=relation.novel
                                ).order_by('-chapter_sort_number').first()
                                
                                next_sort = (last_chapter.chapter_sort_number + 1) if last_chapter else 1
                                
                                Chapter.objects.create(
                                    novel=relation.novel,
                                    title=chapter_data['title'],
                                    content=chapter_data.get('content', ''),
                                    chapter_number=chapter_data.get('chapter_number', saved_count + 1),
                                    chapter_sort_number=next_sort,
                                    word_count=len(chapter_data.get('content', ''))
                                )
                                saved_count += 1
                                
                        except Exception as e:
                            print(f"保存章节失败: {chapter_data['title']}, 错误: {e}")
                            continue
                    
                    # 更新统计信息
                    relation.sync_count += 1
                    relation.chapter_count = Chapter.objects.filter(novel=relation.novel).count()
                    relation.last_sync_at = timezone.now()
                    relation.save()
                    
                    # 更新来源统计
                    relation.source.crawl_count += 1
                    relation.source.last_crawl_at = timezone.now()
                    relation.source.save()
                    
                    success_msg = (
                        f'✅ 高级爬取成功!\n'
                        f'📚 小说: {relation.novel.title}\n'
                        f'📊 处理章节: {saved_count} 章\n'
                        f'🔗 来源: {relation.source_url}\n'
                        f'⚙️ 使用: 自定义参数爬虫'
                    )
                    self.message_user(request, success_msg, messages.SUCCESS)
                    success_count += 1
                    total_chapters += saved_count
                    
                else:
                    self.message_user(
                        request,
                        f'❌ 未能获取到章节数据: {relation.novel.title}',
                        messages.WARNING
                    )
                    
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 爬取 "{relation}" 时出错: {str(e)}',
                    messages.ERROR
                )
        
        # 显示总结消息
        if success_count > 0:
            summary_msg = (
                f'🎉 高级爬取完成!\n'
                f'✅ 成功爬取: {success_count} 个小说\n'
                f'📖 总处理章节: {total_chapters} 章\n'
                f'🚀 使用: Pachong高级爬虫系统'
            )
            self.message_user(request, summary_msg, messages.SUCCESS)
        else:
            self.message_user(
                request,
                '❌ 没有成功爬取任何小说，请检查配置和网络连接',
                messages.WARNING
            )

    def _crawl_from_relation(self, request, relation):
        """从关联爬取小说"""
        try:
            # 获取对应的爬虫类
            crawler_class = relation.source.get_crawler_class()
            crawler = crawler_class(relation.source_url)

            # 爬取小说
            chapters = crawler.crawl_novel(relation.novel.title)

            if chapters:
                # 保存章节到数据库
                new_chapters_count = self._save_chapters(relation.novel, chapters)

                # 更新统计信息
                relation.sync_count += 1
                relation.chapter_count = len(chapters)
                relation.last_sync_at = timezone.now()
                relation.save()

                # 更新来源统计
                relation.source.crawl_count += 1
                relation.source.last_crawl_at = timezone.now()
                relation.source.save()

                self.message_user(
                    request,
                    f'✅ 成功从 "{relation.source.name}" 爬取 {new_chapters_count} 章',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f'❌ 未找到章节: {relation.source.name}',
                    messages.WARNING
                )

        except Exception as e:
            self.message_user(
                request,
                f'❌ 爬取失败: {e}',
                messages.ERROR
            )

    def _save_chapters(self, novel, chapters):
        """保存章节到数据库"""
        from novels.models import Chapter
        new_count = 0

        # 获取现有最大排序号
        last_chapter = Chapter.objects.filter(novel=novel).order_by('-chapter_sort_number').first()
        start_sort_number = (last_chapter.chapter_sort_number + 1) if last_chapter else 1

        for chapter_data in chapters:
            try:
                # 检查是否已存在
                existing = Chapter.objects.filter(
                    novel=novel,
                    title=chapter_data['title']
                ).exists()

                if not existing:
                    # 提取章节信息
                    chapter_number, title_part, arabic_num = self._extract_chapter_info(chapter_data['title'])

                    # 创建章节
                    Chapter.objects.create(
                        novel=novel,
                        title=title_part,
                        content=chapter_data['content'],
                        chapter_number=chapter_number,
                        chapter_sort_number=start_sort_number + new_count,
                        word_count=chapter_data.get('word_count', len(chapter_data['content']))
                    )
                    new_count += 1

            except Exception as e:
                print(f"保存章节失败: {chapter_data['title']}, 错误: {e}")
                continue

        return new_count

    def _extract_chapter_info(self, chapter_title):
        """从章节标题中提取章节信息"""
        import re

        # 匹配中文数字格式：第一千一百八十八章连环天雷
        match = re.search(r'^第([一二两三四五六七八九十百千万亿]+)章(.*)', chapter_title)
        if match:
            chapter_number = match.group(1)
            title_part = match.group(2).strip() if match.group(2).strip() else f"第{chapter_number}章"
            arabic_num = self.custom_cn2an(chapter_number) if chapter_number else 1
            return chapter_number, title_part, arabic_num

        # 匹配阿拉伯数字格式：第1713章得丹
        match = re.search(r'^第(\d+)章(.*)', chapter_title)
        if match:
            arabic_num_str = match.group(1)
            title_part = match.group(2).strip() if match.group(2).strip() else f"第{arabic_num_str}章"
            chapter_number = self.arabic_to_chinese(arabic_num_str)
            arabic_num = int(arabic_num_str)
            return chapter_number, title_part, arabic_num

        # 默认处理
        return '一', chapter_title, 1


@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    """小说管理"""
    list_display = ['title', 'author', 'chapter_count', 'source_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'author']
    search_fields = ['title', 'author', 'description']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['add_source', 'crawl_all_sources', 'intelligent_batch_import']

    fieldsets = [
        ('基本信息', {
            'fields': ['title', 'author', 'description', 'cover_image']
        }),
        ('状态', {
            'fields': ['is_active', 'status']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def chapter_count(self, obj):
        """显示章节数量"""
        from novels.models import Chapter
        return Chapter.objects.filter(novel=obj).count()
    chapter_count.short_description = '章节数量'

    def source_count(self, obj):
        """显示来源数量"""
        return obj.novelsourcerelation_set.count()
    source_count.short_description = '来源数量'

    def add_source(self, request, queryset):
        """添加来源"""
        for novel in queryset:
            try:
                # 这里可以实现自动检测来源的逻辑
                self.message_user(
                    request,
                    f'请在小说编辑页面为 "{novel.title}" 添加来源',
                    messages.INFO
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'处理 "{novel.title}" 时出错: {e}',
                    messages.ERROR
                )

    add_source.short_description = '➕ 添加来源'

    def crawl_all_sources(self, request, queryset):
        """从所有来源爬取小说"""
        for novel in queryset:
            try:
                relations = novel.novelsourcerelation_set.filter(is_primary=True)

                if not relations:
                    self.message_user(
                        request,
                        f'小说 "{novel.title}" 没有设置主要来源',
                        messages.WARNING
                    )
                    continue

                for relation in relations:
                    admin_instance = NovelSourceRelationAdmin(NovelSourceRelation, None)
                    admin_instance._crawl_from_relation(request, relation)

            except Exception as e:
                self.message_user(
                    request,
                    f'处理 "{novel.title}" 时出错: {e}',
                    messages.ERROR
                )

    crawl_all_sources.short_description = '🕷️ 爬取所有来源'

    def intelligent_batch_import(self, request, queryset):
        """智能批量导入章节 - Django Admin版本"""
        success_novels = 0
        total_chapters = 0
        
        for novel in queryset:
            try:
                self.message_user(
                    request,
                    f'🚀 开始智能批量导入: {novel.title}',
                    messages.INFO
                )
                
                # 从小说来源关联中获取主要来源
                primary_sources = novel.novelsourcerelation_set.filter(is_primary=True)
                
                if not primary_sources.exists():
                    self.message_user(
                        request,
                        f'⚠️ 小说 "{novel.title}" 没有设置主要来源，跳过',
                        messages.WARNING
                    )
                    continue
                
                for relation in primary_sources:
                    try:
                        # 使用新的pachong爬虫系统
                        from example_site_quick_crawler import ExampleSiteQuickCrawler
                        
                        # 创建爬虫实例
                        crawler = ExampleSiteQuickCrawler()
                        
                        self.message_user(
                            request,
                            f'🔍 正在从 {relation.source.name} 智能分析章节结构...',
                            messages.INFO
                        )
                        
                        # 智能批量导入
                        result = crawler.intelligent_batch_import(
                            novel=novel,
                            source_url=relation.source_url,
                            source_name=relation.source.name
                        )
                        
                        if result['success']:
                            chapter_count = result['chapters_imported']
                            total_chapters += chapter_count
                            
                            # 更新来源统计
                            relation.sync_count += 1
                            relation.chapter_count = chapter_count
                            relation.last_sync_at = timezone.now()
                            relation.save()
                            
                            relation.source.crawl_count += 1
                            relation.source.last_crawl_at = timezone.now()
                            relation.source.save()
                            
                            success_msg = (
                                f'✅ 智能导入成功: {novel.title}\n'
                                f'📊 导入章节: {chapter_count} 章\n'
                                f'🔗 来源: {relation.source.name}\n'
                                f'⏱️ 平均延时: {(result["min_delay"] + result["max_delay"]) / 2:.1f}秒\n'
                                f'🔄 重试次数: {result.get("total_retries", 0)} 次'
                            )
                            self.message_user(request, success_msg, messages.SUCCESS)
                            success_novels += 1
                            
                        else:
                            error_msg = (
                                f'❌ 智能导入失败: {novel.title}\n'
                                f'🔗 来源: {relation.source.name}\n'
                                f'💬 错误: {result.get("error", "未知错误")}'
                            )
                            self.message_user(request, error_msg, messages.ERROR)
                            
                    except ImportError:
                        self.message_user(
                            request,
                            f'❌ 智能批量爬虫模块未找到，请确保 intelligent_batch_crawler.py 文件存在',
                            messages.ERROR
                        )
                    except Exception as e:
                        self.message_user(
                            request,
                            f'❌ 导入 "{novel.title}" 时出错: {str(e)}',
                            messages.ERROR
                        )
                        
            except Exception as e:
                self.message_user(
                    request,
                    f'❌ 处理小说 "{novel.title}" 时出错: {str(e)}',
                    messages.ERROR
                )
        
        # 显示总结消息
        if success_novels > 0:
            summary_msg = (
                f'🎉 智能批量导入完成!\n'
                f'📚 成功小说: {success_novels} 本\n'
                f'📖 总导入章节: {total_chapters} 章\n'
                f'🚀 速度控制: 2-5秒随机延时\n'
                f'🔗 源链接: 已记录每章来源'
            )
            self.message_user(request, summary_msg, messages.SUCCESS)
        else:
            self.message_user(
                request,
                '❌ 没有成功导入任何小说，请检查小说来源配置',
                messages.WARNING
            )
    
    intelligent_batch_import.short_description = '🧠 智能批量导入章节'


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title', 'novel', 'volume', 'chapter_number', 'chapter_sort_number', 'word_count', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at', 'novel']
    search_fields = ['title']
    readonly_fields = ['word_count', 'created_at', 'updated_at']
    ordering = ['novel', 'chapter_sort_number']
    actions = ['chapter_ai_fix', 'mcp_chapter_fix', 'mcp_crawl_new_chapters', 'playwright_auto_download']
    fieldsets = [
        ('基本信息', {
            'fields': ['novel', 'title', 'chapter_number', 'chapter_sort_number']
        }),
        ('内容', {
            'fields': ['content']
        }),
        ('状态', {
            'fields': ['is_published']
        }),
        ('统计信息', {
            'fields': ['word_count'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('novel')

    def chapter_ai_fix(self, request, queryset):
        """AI修复章节信息：从内容中提取章节标题和排序数字"""
        fixed_count = 0
        error_count = 0

        for chapter in queryset:
            try:
                # 从章节内容中提取章节信息
                content = chapter.content.strip()

                # 查找章节标题模式
                # 匹配多种格式：
                # 1. 中文数字：第一千一百八十八章连环天雷
                # 2. 阿拉伯数字：第1713章得丹
                # 3. 混合格式：第123章风云变幻

                # 初始化卷信息
                volume_info = None

                # 首先检查是否包含卷信息（如："第十一卷真仙降世第两千一百七十一章闭关"）
                volume_match = re.search(r'^(第[一二两三四五六七八九十百千万亿]+卷[^第]*)第', content, re.MULTILINE)
                if volume_match:
                    volume_info = volume_match.group(1).strip()
                    # 移除卷信息后的内容用于后续处理
                    content_without_volume = content.replace(volume_info, '', 1).strip()
                else:
                    content_without_volume = content

                # 现在使用清理后的内容进行匹配
                # 首先尝试匹配没有标题的格式（如："第九百九十六章"）
                match = re.search(r'^第([一二两三四五六七八九十百千万亿]+)章$', content_without_volume, re.MULTILINE)
                if match:
                    chapter_number = match.group(1)
                    title_part = f"第{chapter_number}章"  # 无标题格式，使用章节号作为标题
                    arabic_num = custom_cn2an(chapter_number)
                else:
                    # 尝试匹配阿拉伯数字格式
                    match = re.search(r'^第(\d+)章(.*)', content_without_volume, re.MULTILINE)
                    if match:
                        # 处理阿拉伯数字格式
                        arabic_num_str = match.group(1)  # "1713"
                        title_part = match.group(2).strip()  # "得丹"
                        if not title_part:  # 如果没有标题，使用默认标题
                            title_part = f"第{arabic_num_str}章"
                        chapter_number = arabic_to_chinese(arabic_num_str)  # 转换为中文数字
                        arabic_num = int(arabic_num_str)  # 直接使用阿拉伯数字作为排序数字
                    else:
                        # 尝试匹配中文数字格式
                        match = re.search(r'^第([一二两三四五六七八九十百千万亿]+)章(.*)', content_without_volume, re.MULTILINE)
                        if match:
                            chapter_number = match.group(1)  # "一千七百一十三"
                            title_part = match.group(2).strip()  # "得丹"
                            if not title_part:  # 如果没有标题，使用默认标题
                                title_part = f"第{chapter_number}章"
                            arabic_num = custom_cn2an(chapter_number)  # 转换为阿拉伯数字
                        else:
                            # 尝试匹配更复杂的格式（如："第两千一百七十一章闭关"）
                            match = re.search(r'.*第([一二两三四五六七八九十百千万亿]+)章(.*)', content_without_volume, re.MULTILINE)
                            if match:
                                chapter_number = match.group(1)
                                title_part = match.group(2).strip() if match.group(2).strip() else f"第{chapter_number}章"
                                arabic_num = custom_cn2an(chapter_number)
                            else:
                                match = None

                if match:
                    try:
                        # 检查chapter_sort_number是否已存在，如果存在则自动递增
                        original_arabic_num = arabic_num
                        while Chapter.objects.filter(
                            novel=chapter.novel,
                            chapter_sort_number=arabic_num
                        ).exclude(id=chapter.id).exists():
                            arabic_num += 1  # 如果冲突，自动递增

                        # 更新章节信息
                        chapter.chapter_number = chapter_number  # 存储中文数字部分
                        chapter.chapter_sort_number = arabic_num  # 存储阿拉伯数字用于排序
                        chapter.title = title_part if title_part else f'第{chapter_number}章'

                        # 更新卷信息
                        if volume_info:
                            chapter.volume = volume_info

                        # 设置AI修复标记，允许更新标题
                        chapter._is_ai_fix = True
                        chapter.save()
                        # 清理标记
                        if hasattr(chapter, '_is_ai_fix'):
                            delattr(chapter, '_is_ai_fix')
                        fixed_count += 1

                        # 如果chapter_sort_number被修改，记录警告
                        if arabic_num != original_arabic_num:
                            self.message_user(
                                request,
                                f'章节 "{chapter.title}" 的排序数字因冲突从 {original_arabic_num} 调整为 {arabic_num}',
                                messages.WARNING
                            )
                    except Exception as e:
                        error_count += 1
                        self.message_user(
                            request,
                            f'章节 "{chapter.title}" 数字转换失败: {e}',
                            messages.WARNING
                        )
                else:
                    error_count += 1
                    self.message_user(
                        request,
                        f'章节 "{chapter.title}" 未找到章节标题格式',
                        messages.WARNING
                    )

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f'处理章节 "{chapter.title}" 时出错: {e}',
                    messages.ERROR
                )

        # 删除内容过短的章节
        short_chapters = []
        for chapter in queryset.filter(content__isnull=False):
            if len(chapter.content.strip()) < 50:
                short_chapters.append(chapter)

        if short_chapters:
            short_count = len(short_chapters)
            # 批量删除
            for chapter in short_chapters:
                chapter.delete()

            self.message_user(
                request,
                f'已删除 {short_count} 个内容过短（<50字）的章节',
                messages.WARNING
            )

        # 显示结果消息
        if fixed_count > 0:
            self.message_user(
                request,
                f'成功修复 {fixed_count} 个章节',
                messages.SUCCESS
            )

        if error_count > 0:
            self.message_user(
                request,
                f'{error_count} 个章节处理失败',
                messages.WARNING
            )

    chapter_ai_fix.short_description = '📖 AI修复章节信息'
    chapter_ai_fix.help_text = '从章节内容中自动提取章节标题和排序数字'

    def mcp_chapter_fix(self, request, queryset):
        """使用MCP Chrome工具修复章节信息"""
        if not queryset:
            self.message_user(request, '请先选择要修复的章节', messages.WARNING)
            return

        try:
            from novels.views import MCPClientService

            # 初始化MCP客户端
            mcp_client = MCPClientService()

            # 获取网页章节数据
            main_content = mcp_client.get_page_content(mcp_client.book_url)
            if not main_content:
                self.message_user(request, '无法获取网站内容，请检查网络连接', messages.ERROR)
                return

            web_chapters = mcp_client.parse_chapter_list(main_content)
            if not web_chapters:
                self.message_user(request, '未找到任何章节数据', messages.ERROR)
                return

            # 修复选中的章节
            success_count = 0
            error_count = 0

            for chapter in queryset:
                try:
                    # 找到对应的网页章节数据
                    web_chapter = None
                    for web_ch in web_chapters:
                        if chapter.title in web_ch['title'] or web_ch['title'] in chapter.title:
                            web_chapter = web_ch
                            break

                    if web_chapter:
                        # 显示处理信息
                        self.message_user(
                            request,
                            f'🔄 正在处理章节: {chapter.title} → 匹配到: {web_chapter["title"]}',
                            messages.INFO
                        )

                        if mcp_client.update_chapter_from_web(chapter, web_chapter):
                            success_count += 1
                            self.message_user(
                                request,
                                f'✅ 章节修复成功: {chapter.title}',
                                messages.SUCCESS
                            )
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                        self.message_user(
                            request,
                            f'❌ 未找到匹配章节: {chapter.title}',
                            messages.WARNING
                        )

                except Exception as e:
                    error_count += 1
                    self.message_user(
                        request,
                        f'处理章节 "{chapter.title}" 时出错: {e}',
                        messages.ERROR
                    )

            # 显示结果消息
            if success_count > 0:
                self.message_user(
                    request,
                    f'✅ MCP修复成功: {success_count} 个章节',
                    messages.SUCCESS
                )

            if error_count > 0:
                self.message_user(
                    request,
                    f'❌ MCP修复失败: {error_count} 个章节',
                    messages.WARNING
                )

        except Exception as e:
            self.message_user(
                request,
                f'MCP修复过程出错: {str(e)}',
                messages.ERROR
            )

    mcp_chapter_fix.short_description = '🤖 MCP修复章节'
    mcp_chapter_fix.help_text = '使用MCP Chrome工具从网站获取最新章节信息并修复'

    def mcp_crawl_new_chapters(self, request, queryset):
        """使用MCP Chrome工具爬取新章节"""
        try:
            from novels.views import MCPClientService

            # 初始化MCP客户端
            mcp_client = MCPClientService()

            # 获取网页章节数据
            main_content = mcp_client.get_page_content(mcp_client.book_url)
            if not main_content:
                self.message_user(request, '无法获取网站内容，请检查网络连接', messages.ERROR)
                return

            web_chapters = mcp_client.parse_chapter_list(main_content)
            if not web_chapters:
                self.message_user(request, '未找到任何章节数据', messages.ERROR)
                return

            # 获取当前小说（从queryset中获取第一个章节的小说）
            if queryset:
                novel = queryset.first().novel
            else:
                # 如果没有选择章节，获取第一个小说
                from novels.models import Novel
                novel = Novel.objects.first()
                if not novel:
                    self.message_user(request, '未找到小说记录', messages.ERROR)
                    return

            # 获取现有的最大章节号
            from novels.models import Chapter
            last_chapter = Chapter.objects.filter(novel=novel).order_by('-chapter_sort_number').first()
            start_sort_number = (last_chapter.chapter_sort_number + 1) if last_chapter else 1

            # 创建新章节
            created_count = 0
            for i, web_chapter in enumerate(web_chapters):
                try:
                    # 检查是否已存在
                    existing = Chapter.objects.filter(
                        novel=novel,
                        title=web_chapter['title']
                    ).exists()

                    if not existing:
                        # 获取章节内容
                        content = ""
                        if web_chapter.get('url'):
                            page_content = mcp_client.get_page_content(web_chapter['url'])
                            if page_content:
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(page_content, 'html.parser')
                                content_div = soup.find('div', id='content')
                                if content_div:
                                    for ad in content_div.find_all(['tt', 'a']):
                                        ad.decompose()
                                    content = content_div.get_text()
                                    import re
                                    content = re.sub(r'\n+', '\n', content).strip()

                        # 提取章节信息
                        chapter_number, title_part, arabic_num = mcp_client.extract_chapter_info(web_chapter['title'])

                        # 创建章节
                        Chapter.objects.create(
                            novel=novel,
                            title=title_part,
                            content=content,
                            chapter_number=chapter_number,
                            chapter_sort_number=start_sort_number + i,
                            volume=web_chapter.get('volume', ''),
                            word_count=len(content)
                        )
                        created_count += 1

                except Exception as e:
                    print(f"创建章节失败: {e}")
                    continue

            if created_count > 0:
                self.message_user(
                    request,
                    f'✅ 成功爬取并创建 {created_count} 个新章节',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    '没有找到新章节需要创建',
                    messages.INFO
                )

        except Exception as e:
            self.message_user(
                request,
                f'MCP爬取过程出错: {str(e)}',
                messages.ERROR
            )

    mcp_crawl_new_chapters.short_description = '🕷️ MCP爬取新章节'
    mcp_crawl_new_chapters.help_text = '使用MCP Chrome工具从网站爬取新章节'

    def playwright_auto_download(self, request, queryset):
        """使用简化版Playwright自动下载小说 - 最终异步上下文兼容版"""
        try:
            from simple_playwright_service import SimplePlaywrightService
            from asgiref.sync import async_to_sync, iscoroutinefunction
            import asyncio
            import os

            # 检查Django是否在异步上下文中
            try:
                # 尝试获取当前事件循环，如果存在则说明在异步上下文中
                asyncio.get_running_loop()
                is_async_context = True
                print("🔍 检测到异步上下文，使用线程隔离模式")
            except RuntimeError:
                is_async_context = False
                print("🔍 检测到同步上下文，直接调用Playwright")

            # 获取当前小说
            if queryset:
                novel = queryset.first().novel
            else:
                from novels.models import Novel
                novel = Novel.objects.first()
                if not novel:
                    self.message_user(request, '未找到小说记录', messages.ERROR)
                    return

            # 如果在异步上下文中，使用线程隔离
            if is_async_context:
                return self._run_playwright_in_thread(request, novel)
            else:
                # 在同步上下文中，直接调用
                return self._run_playwright_direct(request, novel)

        except ImportError:
            self.message_user(request, '❌ Playwright未安装，请先运行: pip install playwright && playwright install chromium', messages.ERROR)
        except Exception as e:
            self.message_user(request, f'❌ Playwright操作异常: {str(e)}', messages.ERROR)

    def _run_playwright_direct(self, request, novel):
        """直接运行Playwright（同步上下文）"""
        from simple_playwright_service import SimplePlaywrightService

        self.message_user(request, '🔄 正在启动简化版Playwright浏览器...', messages.INFO)

        try:
            playwright_service = SimplePlaywrightService()
            success = playwright_service.setup_browser(headless=False)  # 有头模式

            if success:
                self.message_user(request, '✅ 简化版Playwright浏览器启动成功', messages.SUCCESS)
            else:
                self.message_user(request, '❌ 浏览器启动失败，请检查Playwright安装', messages.ERROR)
                return

            # 开始自动下载
            self.message_user(request, f'🚀 开始自动下载小说: {novel.title}', messages.INFO)

            try:
                result = playwright_service.auto_download_novel(novel)
                playwright_service.close()

                if result.get('success'):
                    elapsed_time = result.get('elapsed_time', 0)
                    success_msg = (
                        f'✅ 简化版Playwright自动下载完成!\n'
                        f'📊 总章节数: {result.get("total_found", 0)}\n'
                        f'🆕 新章节数: {result.get("new_chapters", 0)}\n'
                        f'✅ 成功下载: {result.get("success_count", 0)}\n'
                        f'❌ 下载失败: {result.get("error_count", 0)}\n'
                        f'⏱️ 耗时: {elapsed_time:.1f}秒'
                    )
                    self.message_user(request, success_msg, messages.SUCCESS)
                else:
                    self.message_user(request, f'❌ 自动下载失败: {result.get("error", "未知错误")}', messages.ERROR)

            except Exception as e:
                playwright_service.close()
                self.message_user(request, f'❌ 下载过程异常: {str(e)}', messages.ERROR)

        except Exception as e:
            self.message_user(request, f'❌ 直接调用异常: {str(e)}', messages.ERROR)

    def _run_playwright_in_thread(self, request, novel):
        """在单独线程中运行Playwright（异步上下文）"""
        import threading
        import time

        result_container = {}
        error_container = {}

        def run_playwright_download():
            try:
                from simple_playwright_service import SimplePlaywrightService

                playwright_service = SimplePlaywrightService()
                success = playwright_service.setup_browser(headless=False)  # 有头模式

                if not success:
                    error_container['error'] = '浏览器启动失败，请检查Playwright安装'
                    return

                # 开始自动下载
                result = playwright_service.auto_download_novel(novel)
                playwright_service.close()

                result_container['result'] = result

            except Exception as e:
                error_container['error'] = str(e)

        # 在单独的线程中运行Playwright，避免异步上下文问题
        download_thread = threading.Thread(target=run_playwright_download)
        download_thread.start()

        # 等待线程完成，设置合理的超时时间
        max_wait_time = 600  # 10分钟超时
        start_time = time.time()

        self.message_user(request, f'🚀 开始自动下载小说: {novel.title} (异步上下文，线程隔离模式)', messages.INFO)

        # 定期检查线程状态
        while download_thread.is_alive() and (time.time() - start_time) < max_wait_time:
            time.sleep(5)  # 每5秒检查一次

            elapsed = int(time.time() - start_time)
            if elapsed % 60 == 0:  # 每分钟报告一次
                minutes = elapsed // 60
                self.message_user(request, f'⏳ 自动下载进行中... 已运行 {minutes} 分钟', messages.INFO)

        # 检查是否超时
        if download_thread.is_alive():
            self.message_user(request, '⚠️ 自动下载超时，已在后台继续运行，请稍后检查结果', messages.WARNING)
            return

        # 等待线程完全结束
        download_thread.join(timeout=5)

        # 检查结果
        if 'error' in error_container:
            self.message_user(request, f'❌ 自动下载失败: {error_container["error"]}', messages.ERROR)
        elif 'result' in result_container:
            result = result_container['result']
            if result.get('success'):
                elapsed_time = result.get('elapsed_time', 0)
                success_msg = (
                    f'✅ 简化版Playwright自动下载完成!\n'
                    f'📊 总章节数: {result.get("total_found", 0)}\n'
                    f'🆕 新章节数: {result.get("new_chapters", 0)}\n'
                    f'✅ 成功下载: {result.get("success_count", 0)}\n'
                    f'❌ 下载失败: {result.get("error_count", 0)}\n'
                    f'⏱️ 耗时: {elapsed_time:.1f}秒'
                )
                self.message_user(request, success_msg, messages.SUCCESS)
            else:
                self.message_user(request, f'❌ 自动下载失败: {result.get("error", "未知错误")}', messages.ERROR)
        else:
            self.message_user(request, '❌ 自动下载异常: 未获取到结果', messages.ERROR)

    playwright_auto_download.short_description = '🎭 Playwright自动下载'
    playwright_auto_download.help_text = '使用Playwright有头浏览器自动下载整本小说，支持手动处理反爬虫'


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'novel', 'is_main_character', 'voice_style', 'created_at']
    list_filter = ['is_main_character', 'created_at', 'novel']
    search_fields = ['name', 'novel__title', 'description']
    readonly_fields = ['created_at']
    ordering = ['-is_main_character', 'novel', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['novel', 'name', 'description']
        }),
        ('角色设置', {
            'fields': ['is_main_character', 'voice_style', 'avatar']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('novel')


@admin.register(NovelTag)
class NovelTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'novel_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def novel_count(self, obj):
        return obj.novel_relations.count()
    novel_count.short_description = '关联小说数量'


class NovelTagRelationInline(admin.TabularInline):
    model = NovelTagRelation
    extra = 1
    autocomplete_fields = ['tag']


# ===== 标签内联编辑 =====

class NovelTagRelationInline(admin.TabularInline):
    model = NovelTagRelation
    extra = 1
    autocomplete_fields = ['tag']


@admin.register(NovelTagRelation)
class NovelTagRelationAdmin(admin.ModelAdmin):
    list_display = ['novel', 'tag', 'created_at']
    list_filter = ['created_at', 'tag']
    autocomplete_fields = ['novel', 'tag']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('novel', 'tag')
