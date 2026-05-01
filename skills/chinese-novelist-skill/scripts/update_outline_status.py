#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 00-大纲.md 的章节状态、表格、摘要和累计统计。

示例：
python3 skills/chinese-novelist/scripts/update_outline_status.py \
  --outline novels/午夜列车/00-大纲.md \
  --chapter 1 \
  --title 最后一班列车 \
  --event 主角在末班地铁上遇到失踪者留下的录音 \
  --hook 他发现录音里的报站声来自十年前废弃的车站 \
  --status done \
  --word-count 3386 \
  --summary "林策在调查一起失踪案时登上末班地铁，发现失踪者留下的录音..."
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SECTION_WAITING = "### 待创作"
SECTION_DOING = "### 进行中"
SECTION_DONE = "### 已完成"
TABLE_HEADER = "## 章节规划"
SUMMARY_HEADER = "## 章节摘要"
STATS_HEADER = "## 字数统计"

STATUS_MAP = {
    "todo": "待创作",
    "doing": "进行中",
    "done": "已完成",
}

CHECKBOX_MAP = {
    "todo": "[ ]",
    "doing": "[ ]",
    "done": "[x]",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="更新小说大纲中的章节状态")
    p.add_argument("--outline", required=True, help="00-大纲.md 路径")
    p.add_argument("--chapter", required=True, type=int, help="章节号，整数")
    p.add_argument("--title", default="", help="章节标题；留空则尝试从大纲读取")
    p.add_argument("--event", default="", help="核心事件；留空则尝试从大纲读取")
    p.add_argument("--hook", default="", help="结尾钩子；留空则尝试从大纲读取")
    p.add_argument("--status", required=True, choices=["todo", "doing", "done"], help="章节状态")
    p.add_argument("--word-count", type=int, default=0, help="章节字数")
    p.add_argument("--summary", default="", help="章节摘要")
    return p.parse_args()


def chapter_label(chapter: int) -> str:
    return f"第{chapter}章"


def load_outline_row(text: str, chapter: int) -> dict[str, str]:
    pattern = re.compile(
        rf"^\| 第{chapter}章 \|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return {}
    return {
        "title": match.group(1).strip(),
        "event": match.group(2).strip(),
        "hook": match.group(3).strip(),
        "word_count": match.group(4).strip(),
        "status": match.group(5).strip(),
    }


def choose(value: str, fallback: str, empty_markers: tuple[str, ...] = ("", "待定", "待规划")) -> str:
    value = (value or "").strip()
    if value and value not in empty_markers:
        return value
    fallback = (fallback or "").strip()
    if fallback and fallback not in empty_markers:
        return fallback
    return "待补充"


def build_item(chapter: int, title: str, event: str, status: str, word_count: int) -> str:
    label = chapter_label(chapter)
    checkbox = CHECKBOX_MAP[status]
    if status == "done":
        return f"- {checkbox} {label}：{title} - {event}（{word_count}字）"
    return f"- {checkbox} {label}：{title} - {event}"


def split_lines(text: str) -> list[str]:
    return text.splitlines()


def find_line(lines: list[str], needle: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == needle:
            return i
    raise ValueError(f"未找到段落标题: {needle}")


def extract_section_items(lines: list[str], start_heading: str, next_heading: str) -> tuple[int, int, list[str]]:
    start = find_line(lines, start_heading) + 1
    end = find_line(lines, next_heading)
    body = lines[start:end]
    items = [line for line in body if line.strip().startswith("- ") and "暂无" not in line]
    return start, end, items


def chapter_sort_key(item: str) -> int:
    m = re.search(r"第(\d+)章", item)
    return int(m.group(1)) if m else 10**9


def remove_chapter_items(items: list[str], chapter: int) -> list[str]:
    pattern = re.compile(rf"第{chapter}章")
    return [item for item in items if not pattern.search(item)]


def render_items(items: list[str], placeholder_checked: bool = False) -> list[str]:
    if items:
        return sorted(items, key=chapter_sort_key)
    return ["- [x] 暂无" if placeholder_checked else "- [ ] 暂无"]


def update_todo_sections(lines: list[str], chapter: int, title: str, event: str, status: str, word_count: int) -> list[str]:
    waiting_start, waiting_end, waiting_items = extract_section_items(lines, SECTION_WAITING, SECTION_DOING)
    doing_start, doing_end, doing_items = extract_section_items(lines, SECTION_DOING, SECTION_DONE)
    done_start, done_end, done_items = extract_section_items(lines, SECTION_DONE, TABLE_HEADER)

    waiting_items = remove_chapter_items(waiting_items, chapter)
    doing_items = remove_chapter_items(doing_items, chapter)
    done_items = remove_chapter_items(done_items, chapter)

    new_item = build_item(chapter, title, event, status, word_count)
    if status == "todo":
        waiting_items.append(new_item)
    elif status == "doing":
        doing_items.append(new_item)
    else:
        done_items.append(new_item)

    waiting_block = render_items(waiting_items)
    doing_block = render_items(doing_items)
    done_block = render_items(done_items, placeholder_checked=True)

    new_lines = (
        lines[:waiting_start]
        + waiting_block
        + [""]
        + lines[waiting_end:doing_start]
        + doing_block
        + [""]
        + lines[doing_end:done_start]
        + done_block
        + [""]
        + lines[done_end:]
    )
    return new_lines


def update_table(text: str, chapter: int, title: str, event: str, hook: str, status: str, word_count: int) -> str:
    status_label = STATUS_MAP[status]
    pattern = re.compile(rf"^\| 第{chapter}章 \|.*$", re.MULTILINE)
    replacement = f"| 第{chapter}章 | {title} | {event} | {hook or '待定'} | {word_count} | {status_label} |"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text


def compute_stats(text: str) -> tuple[int, int, int]:
    pattern = re.compile(r"^\| 第\d+章 \| .*? \| .*? \| .*? \| (\d+) \| (.*?) \|$", re.MULTILINE)
    completed = 0
    total_words = 0
    total_rows = 0
    for m in pattern.finditer(text):
        total_rows += 1
        wc = int(m.group(1))
        status = m.group(2).strip()
        if status == "已完成":
            completed += 1
            total_words += wc
    return completed, total_words, total_rows


def update_stats(text: str) -> str:
    completed, total_words, total_rows = compute_stats(text)
    progress = f"{int((completed / total_rows) * 100)}%" if total_rows else "0%"
    text = re.sub(r"- (?:\*\*)?已完成章节数(?:\*\*)?：.*", f"- 已完成章节数：{completed} 章", text)
    text = re.sub(r"- (?:\*\*)?累计字数(?:\*\*)?：.*", f"- 累计字数：{total_words} 字", text)
    text = re.sub(r"- (?:\*\*)?完成进度(?:\*\*)?：.*", f"- 完成进度：{progress}", text)
    return text


def update_summary(text: str, chapter: int, title: str, summary: str) -> str:
    if not summary.strip():
        return text

    block = f"### 第{chapter}章：{title}\n**摘要**：{summary.strip()}\n"
    pattern = re.compile(rf"### 第{chapter}章：.*?(?=\n---\n|\n### 第\d+章：|\Z)", re.S)
    if pattern.search(text):
        return pattern.sub(block.rstrip(), text, count=1)

    marker = "## 章节摘要"
    idx = text.find(marker)
    if idx == -1:
        return text + "\n\n" + marker + "\n\n" + block

    tail = text[idx + len(marker):].strip()
    if not tail or "（从第 1 章开始逐章追加）" in tail:
        return text.replace("（从第 1 章开始逐章追加）", block)

    return text.rstrip() + "\n\n---\n\n" + block


def main() -> int:
    args = parse_args()
    outline = Path(args.outline)
    if not outline.exists():
        raise SystemExit(f"文件不存在: {outline}")

    raw_text = outline.read_text(encoding="utf-8")
    row = load_outline_row(raw_text, args.chapter)
    title = choose(args.title, row.get("title", ""))
    event = choose(args.event, row.get("event", ""))
    hook = choose(args.hook, row.get("hook", ""), empty_markers=("", "待定"))

    lines = split_lines(raw_text)
    lines = update_todo_sections(lines, args.chapter, title, event, args.status, args.word_count)
    text = "\n".join(lines) + "\n"
    text = update_table(text, args.chapter, title, event, hook, args.status, args.word_count)
    text = update_stats(text)
    text = update_summary(text, args.chapter, title, args.summary)
    outline.write_text(text, encoding="utf-8")
    print(f"已更新: {outline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
