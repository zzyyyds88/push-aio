"""消息格式兼容层。

职责：
1. 声明每个渠道支持的格式（supported_formats）+ 降级偏好（preferred_format）
2. 调用方传 plain/markdown/html，兼容层自动转换到渠道能接受的格式
3. 渠道按转换后的 content_format 构造自己的 payload，保留原有 payload 结构

设计原则：
- 兼容层是"适配层"不是"限制层"：保留每个渠道的原有格式能力
- 渠道特有的消息类型（钉钉 link/actionCard、飞书 post/card 等）不在标准兼容层范围
- 每个渠道单独适配，不一刀切

格式能力基于官方文档核实，文档存放在 docs/channel-docs/ 目录。
"""
from __future__ import annotations

import html as _html
import re
from typing import Literal

import markdown as _md


# 三种标准格式
ContentFormat = Literal["plain", "markdown", "html"]


def resolve_format(
    requested: str,
    supported: list[str],
    preferred: str,
) -> str:
    """决策最终格式：渠道支持就用请求格式，否则降级到渠道偏好。

    Args:
        requested: 调用方请求的格式 (plain/markdown/html)
        supported: 渠道支持的格式列表
        preferred: 渠道偏好格式（请求格式不支持时降级到这里）

    Returns:
        最终格式 (plain/markdown/html)
    """
    if requested in supported:
        return requested
    return preferred


def convert_content(content: str, from_format: str, to_format: str) -> str:
    """把 content 从 from_format 转换到 to_format。

    转换矩阵：
    | 请求\支持 | plain    | markdown | html |
    |-----------|----------|----------|------|
    | plain     | 直接用   | 直接用   | 转义+\n→<br> |
    | markdown  | strip语法 | 直接用   | markdown库转HTML |
    | html      | strip标签 | html→md | 直接用 |
    """
    if from_format == to_format:
        return content

    # 转换到 plain
    if to_format == "plain":
        if from_format == "markdown":
            return strip_markdown_to_plain(content)
        if from_format == "html":
            return strip_html_to_plain(content)

    # 转换到 html
    if to_format == "html":
        if from_format == "plain":
            return plain_to_html(content)
        if from_format == "markdown":
            return markdown_to_html(content)

    # 转换到 markdown
    if to_format == "markdown":
        if from_format == "plain":
            return content  # plain 可直接当 markdown 用
        if from_format == "html":
            return html_to_markdown(content)

    return content


# ============================ 转换函数 ============================

def strip_markdown_to_plain(text: str) -> str:
    """把 markdown 语法符号 strip 掉，保留纯文本。

    处理常见语法：标题井号、加粗/斜体、代码块、行内代码、链接、图片、列表符号、引用、分隔线。
    """
    # 代码块：保留内容，去掉 ```
    text = re.sub(r"```[^\n]*\n(.*?)```", r"\1", text, flags=re.DOTALL)
    # 行内代码：去掉反引号
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # 图片：![alt](url) → alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # 链接：[text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # 加粗+斜体 ***text*** 或 ___text___
    text = re.sub(r"\*{3}([^*]+)\*{3}", r"\1", text)
    text = re.sub(r"_{3}([^_]+)_{3}", r"\1", text)
    # 加粗 **text** 或 __text__
    text = re.sub(r"\*{2}([^*]+)\*{2}", r"\1", text)
    text = re.sub(r"_{2}([^_]+)_{2}", r"\1", text)
    # 斜体 *text* 或 _text_
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    # 删除线 ~~text~~
    text = re.sub(r"~~([^~]+)~~", r"\1", text)
    # 标题井号
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # 引用 >
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    # 无序列表符号 - * + 在行首
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    # 有序列表符号 1. 2. 等
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    # 分隔线 --- *** ___
    text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)
    return text.strip()


def strip_html_to_plain(text: str) -> str:
    """把 HTML 标签 strip 掉，保留纯文本。"""
    # <br> / <br/> → 换行
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # <p>, </p>, </div>, </li> 等块级标签闭合 → 换行
    text = re.sub(r"</(?:p|div|li|h[1-6]|tr)>", "\n", text, flags=re.IGNORECASE)
    # 去掉所有 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # HTML 实体反转义
    text = _html.unescape(text)
    # 压缩多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def plain_to_html(text: str) -> str:
    """纯文本转 HTML：转义特殊字符 + 换行转 <br>。"""
    escaped = _html.escape(text)
    return escaped.replace("\n", "<br>")


def markdown_to_html(text: str) -> str:
    """markdown 转 HTML，使用 markdown 库。

    支持常见语法：标题、加粗、斜体、代码块、列表、链接、图片、引用、表格等。
    """
    return _md.markdown(
        text,
        extensions=["extra", "codehilite", "tables", "fenced_code"],
        extension_configs={"codehilite": {"guess_lang": False}},
    )


def html_to_markdown(text: str) -> str:
    """HTML 转 markdown（简单转换，处理常见标签）。

    复杂 HTML 建议直接用 html 格式发送，不走这个转换。
    """
    # <br> → 换行
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # <h1>~<h6> → ## text
    for i in range(1, 7):
        text = re.sub(
            rf"<h{i}[^>]*>(.*?)</h{i}>",
            lambda m, level=i: f"{'#' * level} {m.group(1)}",
            text, flags=re.IGNORECASE | re.DOTALL,
        )
    # <strong>/<b> → **text**
    text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    # <em>/<i> → *text*
    text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    # <code> → `text`
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
    # <pre> → ```text```
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda m: f"```\n{m.group(1)}\n```", text, flags=re.IGNORECASE | re.DOTALL)
    # <a href="url">text</a> → [text](url)
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)
    # <img src="url" alt="text"> → ![text](url)
    text = re.sub(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?\s*>', r"![\2](\1)", text, flags=re.IGNORECASE)
    text = re.sub(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*/?\s*>', r"![](\1)", text, flags=re.IGNORECASE)
    # <li> → - text
    text = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: f"- {m.group(1)}", text, flags=re.IGNORECASE | re.DOTALL)
    # <p>, </p>, </div> → 换行
    text = re.sub(r"</?(?:p|div|ul|ol)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # 去掉剩余 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # HTML 实体反转义
    text = _html.unescape(text)
    # 压缩多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
