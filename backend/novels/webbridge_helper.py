#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi WebBridge 辅助工具
用于在 Cloudflare 拦截时打开用户真实浏览器，由用户人工完成验证后获取页面数据。
"""

import json
import uuid
import re
import requests

WEBBRIDGE_URL = "http://127.0.0.1:10086/command"


class WebBridgeError(Exception):
    pass


def _unwrap(result: dict):
    """WebBridge 返回 {ok, data, error}，这里解出实际的 data"""
    if not result.get("ok"):
        raise WebBridgeError(f"WebBridge 调用失败: {result.get('error', result)}")
    return result.get("data", {})


def _call(action: str, args: dict, session: str = None):
    payload = {"action": action, "args": args}
    if session:
        payload["session"] = session
    try:
        resp = requests.post(WEBBRIDGE_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return _unwrap(resp.json())
    except requests.RequestException as e:
        raise WebBridgeError(f"调用 WebBridge 失败: {e}")


def check_status():
    """检查 WebBridge 是否可用"""
    try:
        resp = requests.get("http://127.0.0.1:10086/status", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def open_user_browser(url: str, session: str = None):
    """在用户真实浏览器中打开指定 URL，返回 session 标识"""
    session = session or f"crawler_bypass_{uuid.uuid4().hex[:8]}"
    result = _call("navigate", {"url": url, "newTab": True}, session=session)
    if not result.get("success"):
        raise WebBridgeError(f"无法打开用户浏览器: {result}")
    return session


def get_cookies(session: str):
    """从 WebBridge 指定 session 的页面获取 document.cookie"""
    code = """
    (function() {
        const cookies = {};
        document.cookie.split(';').forEach(function(part) {
            const [k, v] = part.trim().split('=');
            if (k) cookies[k] = decodeURIComponent(v || '');
        });
        return JSON.stringify(cookies);
    })()
    """
    result = _call("evaluate", {"code": code}, session=session)
    # WebBridge evaluate 返回 {type, value}
    if result.get("success") is False:
        raise WebBridgeError(f"无法获取 cookies: {result}")
    try:
        value = result.get("value", "{}")
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def extract_catalog_from_browser(session: str, base_url: str):
    """直接在用户浏览器中解析页面目录，绕过 Cloudflare 和动态渲染"""
    code = """
    (function() {
        const links = Array.from(document.querySelectorAll('a[href*="/book/"]'));
        const chapters = [];
        const seen = new Set();
        links.forEach(a => {
            const text = a.innerText.trim();
            const href = a.getAttribute('href') || '';
            if (text && href.includes('/book/') && href.endsWith('.html') &&
                text.includes('第') && text.includes('章')) {
                const key = href + '|' + text;
                if (seen.has(key)) return;
                seen.add(key);
                const m = text.match(/第(\d+)章/);
                const num = m ? parseInt(m[1], 10) : 0;
                chapters.push({chapter_num: num, title: text, url: href});
            }
        });
        chapters.sort((a, b) => a.chapter_num - b.chapter_num);
        return JSON.stringify({
            title: document.title,
            url: window.location.href,
            chapters: chapters
        });
    })()
    """
    result = _call("evaluate", {"code": code}, session=session)
    if result.get("success") is False:
        raise WebBridgeError(f"无法解析目录: {result}")
    try:
        value = result.get("value", "{}")
        catalog = json.loads(value)
        # 清理标题
        title = catalog.get('title', '')
        title = re.sub(r'免费在线阅读.*', '', title)
        title = re.sub(r'_.*', '', title).strip()
        catalog['title'] = title
        # 补全相对 URL
        for ch in catalog.get('chapters', []):
            if ch.get('url') and not ch['url'].startswith('http'):
                ch['url'] = requests.compat.urljoin(base_url, ch['url'])
        return catalog
    except json.JSONDecodeError:
        return {}
