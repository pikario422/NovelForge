#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化单章节文件。

支持两种模式：
1. 手动模式：通过参数传入标题 / 核心事件 / 钩子
2. 自动模式：从 00-大纲.md 的章节规划表读取缺失信息

示例：
python3 skills/chinese-novelist/scripts/init_chapter.py \
  --novel novels/午夜列车 \
  --chapter 1 \
  --title 最后一班列车 \
  --event 林策在末班地铁上发现失踪者留下的录音 \
  --hook 录音里的报站声来自十年前废弃的车站

python3 skills/chinese-novelist/scripts/init_chapter.py \
  --novel novels/午夜列车 \
  --chapter 2
"""

from __future__ import annotations

import argparse
import subprocess
import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'[\\/:*?"<>|\n\r]'


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="初始化单章节文件")
    p.add_argument("--novel", required=True, help="小说目录，例如 novels/午夜列车")
    p.add_argument("--chapter", required=True, type=int, help="章节号，整数")
    p.add_argument("--title", default="", help="章节标题；留空则尝试从 00-大纲.md 读取")
    p.add_argument("--event", default="", help="核心事件；留空则尝试从 00-大纲.md 读取")
    p.add_argument("--hook", default="", help="章节结尾钩子；留空则尝试从 00-大纲.md 读取")
    p.add_argument("--carry", default="", help="承接上章内容")
    p.add_argument("--next-hint", default="", help="下章预告")
    p.add_argument("--foreshadow", default="", help="伏笔标记")
    p.add_argument("--outline", default="", help="大纲路径，默认 <小说目录>/00-大纲.md")
    p.add_argument("--template", default="", help="章节模板路径，默认使用 skill 自带模板")
    p.add_argument("--force", action="store_true", help="文件已存在时覆盖")
    p.add_argument("--mark-doing", action="store_true", help="初始化后自动把大纲中的该章标记为进行中")
    return p.parse_args()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_template_path() -> Path:
    return skill_root() / "references" / "chapter-template.md"


def sanitize_filename(text: str) -> str:
    text = re.sub(INVALID_FILENAME_CHARS, "-", text).strip()
    return text or "待定"


def chapter_width_from_outline(text: str) -> int:
    nums = [int(x) for x in re.findall(r"\| 第(\d+)章 \|", text)]
    max_num = max(nums) if nums else 0
    return 3 if max_num >= 100 else 2


def load_outline_row(outline_text: str, chapter: int) -> dict[str, str]:
    pattern = re.compile(
        rf"^\| 第{chapter}章 \|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|$",
        re.MULTILINE,
    )
    match = pattern.search(outline_text)
    if not match:
        return {}
    return {
        "title": match.group(1).strip(),
        "event": match.group(2).strip(),
        "hook": match.group(3).strip(),
        "word_count": match.group(4).strip(),
        "status": match.group(5).strip(),
    }


def fill(value: str, fallback: str, empty_markers: tuple[str, ...] = ("", "待定", "待规划")) -> str:
    value = (value or "").strip()
    if value and value not in empty_markers:
        return value
    fallback = (fallback or "").strip()
    if fallback and fallback not in empty_markers:
        return fallback
    return "待补充"


def build_content(template_text: str, chapter_label: str, title: str, event: str, carry: str, hook: str, next_hint: str, foreshadow: str) -> str:
    content = template_text
    content = content.replace("# 第[X]章：[章节标题]", f"# {chapter_label}：{title}")
    content = content.replace("- **核心事件**：[一句话概括本章发生的事]", f"- **核心事件**：{event}")
    content = content.replace("- **承接上章**：[回应上一章的悬念]", f"- **承接上章**：{carry}")
    content = content.replace("- **悬念钩子**：[本章结尾的钩子]", f"- **悬念钩子**：{hook}")
    content = content.replace("[章节正文内容 3000-5000 字，最低不低于 2500 字]", "[待写：目标 1000-1500 中文字；前段尽快立冲突，中段推进事件，结尾留钩子]")
    content = content.replace("- 本章悬念：[简述结尾钩子]", f"- 本章悬念：{hook}")
    content = content.replace("- 下章预告：[可选，1-2句话]", f"- 下章预告：{next_hint}")
    content = content.replace("- 伏笔标记：[如果埋下伏笔，在此记录]", f"- 伏笔标记：{foreshadow}")
    return content.rstrip() + "\n"


def mark_outline_doing(outline_path: Path, chapter: int, title: str, event: str, hook: str) -> None:
    script = Path(__file__).resolve().parent / "update_outline_status.py"
    command = [
        "python3",
        str(script),
        "--outline", str(outline_path),
        "--chapter", str(chapter),
        "--title", title,
        "--event", event,
        "--hook", hook,
        "--status", "doing",
        "--word-count", "0",
    ]
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    if args.chapter <= 0:
        raise SystemExit("章节号必须大于 0")

    novel_dir = Path(args.novel)
    if not novel_dir.exists():
        raise SystemExit(f"小说目录不存在: {novel_dir}")

    outline_path = Path(args.outline) if args.outline else (novel_dir / "00-大纲.md")
    template_path = Path(args.template) if args.template else default_template_path()

    outline_text = ""
    row = {}
    if outline_path.exists():
        outline_text = outline_path.read_text(encoding="utf-8")
        row = load_outline_row(outline_text, args.chapter)

    width = chapter_width_from_outline(outline_text) if outline_text else 2
    chapter_label = f"第{args.chapter:0{width}d}章"

    title = fill(args.title, row.get("title", ""))
    event = fill(args.event, row.get("event", ""))
    hook = fill(args.hook, row.get("hook", ""))
    carry = (args.carry or "").strip() or ("故事开篇，尽快抛出核心冲突" if args.chapter == 1 else "承接上一章发展并快速推进")
    next_hint = (args.next_hint or "").strip() or "待补充"
    foreshadow = (args.foreshadow or "").strip() or "待补充"

    if not template_path.exists():
        raise SystemExit(f"模板不存在: {template_path}")
    template_text = template_path.read_text(encoding="utf-8")

    filename = f"{chapter_label}-{sanitize_filename(title)}.md"
    out_path = novel_dir / filename
    if out_path.exists() and not args.force:
        raise SystemExit(f"文件已存在，若要覆盖请加 --force: {out_path}")

    content = build_content(
        template_text=template_text,
        chapter_label=chapter_label,
        title=title,
        event=event,
        carry=carry,
        hook=hook,
        next_hint=next_hint,
        foreshadow=foreshadow,
    )
    out_path.write_text(content, encoding="utf-8")

    print(f"已初始化章节文件: {out_path}")
    if row:
        print(f"- 已从大纲读取章节信息: 第{args.chapter}章")
    else:
        print("- 未从大纲读取到章节信息，已使用传入参数/默认值")

    if args.mark_doing:
        if not outline_path.exists():
            raise SystemExit(f"无法标记进行中，大纲不存在: {outline_path}")
        mark_outline_doing(outline_path, args.chapter, title, event, hook)
        print(f"- 已将第{args.chapter}章标记为进行中")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
