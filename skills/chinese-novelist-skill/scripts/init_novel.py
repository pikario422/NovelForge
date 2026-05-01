#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化小说项目目录并生成基础文件。

示例：
python skills/chinese-novelist/scripts/init_novel.py \
  --title "午夜列车" \
  --genre "悬疑推理" \
  --chapters 10 \
  --conflict "查明一桩密室杀人案背后的真相"
"""

from __future__ import annotations

import argparse
from pathlib import Path


def pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0%"
    return f"{int((numerator / denominator) * 100)}%"


def build_outline(title: str, genre: str, chapters: int, conflict: str, protagonist: str, tone: str) -> str:
    chapter_rows = []
    todo_rows = []
    for i in range(1, chapters + 1):
        chapter_rows.append(f"| 第{i}章 | 待定 | 待规划 | 待定 | 0 | 待创作 |")
        todo_rows.append(f"- [ ] 第{i}章：待定 - 待规划")

    return f"""# {title} 大纲

## 基本信息
- **题材**：{genre}
- **风格**：{tone or '待补充'}
- **预计章节数**：{chapters} 章
- **目标字数**：整本 1万-2万字；单章 1000-1500 字
- **核心冲突**：{conflict}
- **主角设定**：{protagonist or '待补充'}

## TODO List

### 待创作
{chr(10).join(todo_rows)}

### 进行中
- [ ] 暂无

### 已完成
- [x] 暂无

## 章节规划

| 章节 | 标题 | 核心事件 | 悬念钩子 | 字数 | 状态 |
|-----|------|---------|---------|------|------|
{chr(10).join(chapter_rows)}

## 全书节奏建议
- **默认结构**：优先采用 8章 / 10章 / 12章中短篇结构模板
- **开局要求**：前 1-3 章尽快立主冲突
- **节奏要求**：每章都要有明确事件结果，每 1-2 章尽量给出升级、反转或新信息
- **收尾要求**：结尾集中解决核心冲突，避免拖尾

## 全书悬念线
- **主线悬念**：待补充
- **支线悬念**：待补充
- **终极揭秘**：待补充

## 字数统计
- 已完成章节数：0 章
- 累计字数：0 字
- 完成进度：{pct(0, chapters)}

---

## 章节摘要

（从第 1 章开始逐章追加）
"""


def build_characters(title: str, protagonist: str) -> str:
    return f"""# {title} 人物档案

## 主角

### {protagonist or '[主角姓名待定]'}
- **年龄/职业**：
- **外貌特征**：
- **性格核心**：
- **核心价值观**：
- **最大恐惧**：
- **致命缺陷**：
- **内心渴望**：
- **背景故事**：
- **MBTI**：

## 反派

### [反派姓名待定]
- **年龄/职业**：
- **外貌特征**：
- **性格核心**：
- **核心价值观**：
- **最大欲望**：
- **隐藏弱点**：
- **背景故事**：

## 配角

### [关键配角一]
- **身份**：
- **作用**：
- **与主角关系**：

### [关键配角二]
- **身份**：
- **作用**：
- **与主角关系**：

## 人物关系备注

- 主角 ↔ 反派：
- 主角 ↔ 配角 A：
- 主角 ↔ 配角 B：
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化中文中短篇小说项目目录")
    parser.add_argument("--title", required=True, help="小说名")
    parser.add_argument("--genre", required=True, help="题材，如悬疑/奇幻/言情")
    parser.add_argument("--chapters", required=True, type=int, help="总章节数")
    parser.add_argument("--conflict", required=True, help="核心冲突")
    parser.add_argument("--protagonist", default="", help="主角设定或主角名")
    parser.add_argument("--tone", default="", help="风格，如冷峻/热血/治愈")
    parser.add_argument("--root", default="novels", help="输出根目录，默认 novels")
    parser.add_argument("--force", action="store_true", help="已存在时覆盖 00-大纲.md 和 01-人物档案.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chapters <= 0:
        raise SystemExit("章节数必须大于 0")

    root = Path(args.root)
    novel_dir = root / args.title
    novel_dir.mkdir(parents=True, exist_ok=True)

    outline_path = novel_dir / "00-大纲.md"
    chars_path = novel_dir / "01-人物档案.md"

    if not args.force:
        existing = [p.name for p in (outline_path, chars_path) if p.exists()]
        if existing:
            raise SystemExit(f"以下文件已存在，若要覆盖请加 --force: {', '.join(existing)}")

    outline_path.write_text(
        build_outline(
            title=args.title,
            genre=args.genre,
            chapters=args.chapters,
            conflict=args.conflict,
            protagonist=args.protagonist,
            tone=args.tone,
        ),
        encoding="utf-8",
    )

    chars_path.write_text(
        build_characters(title=args.title, protagonist=args.protagonist),
        encoding="utf-8",
    )

    print(f"已初始化小说目录: {novel_dir}")
    print(f"- {outline_path}")
    print(f"- {chars_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
