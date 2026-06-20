"""
服务化配置管理器（整合版）：从 legacy_pachong/config_manager.py 复制并内聚到 services。
"""

import json
from urllib.parse import urlparse


class ConfigManager:
    """配置文件管理器：生成/更新/校验/导出站点配置"""
    
    def __init__(self):
        self.default_config = {
            "sites": {},
            "global_settings": {
                "default_site": "example_site",
                "output_directory": "./downloads",
                "create_site_subdirectory": True,
                "create_book_subdirectory": True,
                "chapter_content_subdirectory": "章节内容",
                "generate_download_report": True,
                "report_format": "json",
                "log_level": "info",
                "max_concurrent_downloads": 1,
                "browser_config": {
                    "headless": True,
                    "viewport": {"width": 1280, "height": 720},
                    "locale": "zh-CN",
                    "timezone": "Asia/Shanghai"
                }
            },
            "file_templates": {
                "chapter_file": {
                    "header": "标题: {title}\nURL: {url}\n获取状态: {status}\n获取时间: {timestamp}\n\n" + "="*50 + "\n\n",
                    "content": "{content}",
                    "footer": "\n\n" + "="*50 + "\n下载完成"
                }
            },
            "advanced_features": {
                "auto_encoding_detection": True,
                "javascript_processing": False,
                "cloudflare_bypass": False,
                "proxy_support": False,
                "cookie_management": False,
                "content_validation": {
                    "min_content_length": 100,
                    "required_keywords": [],
                    "forbidden_keywords": ["404", "页面不存在", "访问被拒绝"]
                }
            },
            "error_handling": {
                "max_retries": 3,
                "retry_delay": 5000,
                "timeout_handling": "skip",
                "error_log_file": "error.log",
                "continue_on_error": True
            }
        }
    
    def create_site_config(self, site_key, site_name, base_url, **kwargs):
        """创建网站配置：统一结构，便于下载器按站点差异运行"""
        config = {
            "name": site_name,
            "base_url": base_url,
            "encoding": kwargs.get('encoding', 'utf-8'),
            "selectors": {
                "title": kwargs.get('title_selector', 'h1'),
                "content": kwargs.get('content_selector', '.content'),
                "chapter_list": kwargs.get('chapter_list_selector', '.chapter-list a'),
                "next_page": kwargs.get('next_page_selector', '.next-page')
            },
            "url_patterns": {
                "chapter_url_pattern": kwargs.get('chapter_url_pattern', ''),
                "book_url_pattern": kwargs.get('book_url_pattern', ''),
                "relative_url_base": kwargs.get('relative_url_base', base_url)
            },
            "request_config": {
                "headers": kwargs.get('headers', {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }),
                "timeout": kwargs.get('timeout', 30000),
                "wait_for": kwargs.get('wait_for', 'networkidle'),
                "delay_between_requests": kwargs.get('delay', 2000),
                "retry_count": kwargs.get('retry_count', 3),
                "retry_delay": kwargs.get('retry_delay', 5000)
            },
            "content_processing": {
                "title_cleanup": {
                    "remove_patterns": kwargs.get('title_remove_patterns', [r'\s*第\d+章\s*', r'\s*章节\d+\s*']),
                    "replace_patterns": kwargs.get('title_replace_patterns', {})
                },
                "content_cleanup": {
                    "remove_patterns": kwargs.get('content_remove_patterns', [
                        r'<script[^>]*>.*?</script>',
                        r'<style[^>]*>.*?</style>',
                        r'<!--.*?-->',
                        r'\s*广告\s*',
                        r'\s*推荐.*?\s*'
                    ]),
                    "normalize_whitespace": kwargs.get('normalize_whitespace', True)
                }
            },
            "file_naming": {
                "pattern": kwargs.get('filename_pattern', '{title}'),
                "max_filename_length": kwargs.get('max_filename_length', 200),
                "fallback_pattern": kwargs.get('fallback_pattern', '章节_{chapter_id}_{timestamp}')
            }
        }
        
        return config
    
    def add_example_site_config(self):
        """添加示例站点配置：通用选择器/清洗/延时等参数"""
        return self.create_site_config(
            site_key="example_site",
            site_name="示例站点",
            base_url="https://www.example.com",
            title_selector="h2",
            content_selector="#content",
            chapter_list_selector=".chapter-list a",
            content_remove_patterns=[
                r'<script[^>]*>.*?</script>',
                r'<style[^>]*>.*?</style>',
                r'<!--.*?-->',
                r'\s*广告\s*'
            ],
            delay=3000
        )
    
    def add_custom_site(self, site_key, site_name, base_url, selectors, **kwargs):
        """添加自定义网站配置：按传入选择器与参数生成结构化配置"""
        config = self.create_site_config(
            site_key=site_key,
            site_name=site_name,
            base_url=base_url,
            title_selector=selectors.get('title', 'h1'),
            content_selector=selectors.get('content', '.content'),
            chapter_list_selector=selectors.get('chapter_list', '.chapter-list a'),
            **kwargs
        )
        return config
    
    def generate_config_file(self, filename="downloader_config.json", sites=None):
        """生成配置文件：合并默认全局设置与预设站点，输出JSON"""
        config = self.default_config.copy()
        
        # 添加预设网站配置
        if not sites:
            sites = ['example_site']

        for site in sites:
            if site == 'example_site':
                config['sites']['example_site'] = self.add_example_site_config()

        # 保存配置文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"配置文件已生成: {filename}")
        return config
    
    def update_site_config(self, config_file, site_key, updates):
        """更新网站配置：深度合并字典项，保留未修改字段"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if site_key not in config['sites']:
                print(f"网站 {site_key} 不存在")
                return False
            
            # 深度更新配置
            def deep_update(base_dict, update_dict):
                for key, value in update_dict.items():
                    if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_update(config['sites'][site_key], updates)
            
            # 保存更新后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"网站 {site_key} 配置已更新")
            return True
            
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
    
    def validate_config(self, config_file):
        """验证配置文件：检查必需顶级键与站点所需字段/选择器"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            errors = []
            
            # 检查必需的顶级键
            required_keys = ['sites', 'global_settings']
            for key in required_keys:
                if key not in config:
                    errors.append(f"缺少必需的配置项: {key}")
            
            # 检查网站配置
            if 'sites' in config:
                for site_key, site_config in config['sites'].items():
                    site_errors = self._validate_site_config(site_key, site_config)
                    errors.extend(site_errors)
            
            if errors:
                print("配置验证失败:")
                for error in errors:
                    print(f"  - {error}")
                return False
            else:
                print("配置验证通过")
                return True
                
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def _validate_site_config(self, site_key, site_config):
        """验证单个网站配置：逐项检查必填字段与选择器键"""
        errors = []
        
        # 检查必需的网站配置项
        required_site_keys = ['name', 'base_url', 'selectors']
        for key in required_site_keys:
            if key not in site_config:
                errors.append(f"网站 {site_key} 缺少必需配置: {key}")
        
        # 检查选择器配置
        if 'selectors' in site_config:
            required_selectors = ['title', 'content']
            for selector in required_selectors:
                if selector not in site_config['selectors']:
                    errors.append(f"网站 {site_key} 缺少必需选择器: {selector}")
        
        return errors
    
    def list_sites(self, config_file):
        """列出配置文件中的所有网站：打印site_key、名称与base_url"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("配置的网站:")
            for site_key, site_config in config.get('sites', {}).items():
                print(f"  {site_key}: {site_config.get('name', '未知')} ({site_config.get('base_url', '未知')})")
                
        except Exception as e:
            print(f"读取配置失败: {e}")
    
    def export_site_config(self, config_file, site_key, output_file):
        """导出单个网站配置：将指定站点配置写入独立JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if site_key not in config.get('sites', {}):
                print(f"网站 {site_key} 不存在")
                return False
            
            site_config = config['sites'][site_key]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(site_config, f, ensure_ascii=False, indent=2)
            
            print(f"网站 {site_key} 配置已导出到: {output_file}")
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False


__all__ = ["ConfigManager"]


