#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对平台热榜快照（标题列表）做启发式分析。
输入文件每行一个样本，支持前缀排名、序号、项目符号。

示例：
python3 skills/chinese-novelist/scripts/analyze_rank_snapshot.py \
  --input data/fanqie-top20.txt \
  --platform fanqie \
  --top 20
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

GENRE_KEYWORDS = {
    "悬疑": ["悬疑", "凶案", "失踪", "真相", "诡", "密室", "尸", "追凶", "凶手", "命案"],
    "言情": ["恋", "婚", "前夫", "前妻", "竹马", "白月光", "追妻", "告白", "暗恋", "离婚"],
    "历史": ["东宫", "皇", "帝", "太子", "朝堂", "权臣", "宫", "侯府", "庶", "将军"],
    "现实": ["职场", "北漂", "房贷", "家庭", "相亲", "中年", "公司", "创业"],
    "奇幻": ["仙", "宗门", "灵", "魔", "神", "天道", "圣", "秘境", "修仙"],
    "科幻": ["星", "机甲", "AI", "人工智能", "宇宙", "末日", "未来", "基因", "深空"],
    "武侠": ["江湖", "少侠", "门派", "镖局", "武林", "刀", "剑", "掌门"],
    "都市逆袭": ["重生", "逆袭", "翻盘", "首富", "打脸", "归来", "觉醒", "豪门"],
}

PROTAGONIST_KEYWORDS = {
    "失势再起": ["重生", "归来", "翻盘", "逆袭", "复仇"],
    "调查者": ["警", "记者", "侦探", "法医", "调查", "律师"],
    "普通人卷入": ["意外", "被迫", "误入", "突然", "卷入"],
    "权力边缘人": ["庶", "弃子", "寒门", "侧妃", "养女", "赘婿"],
    "关系受害者": ["离婚", "前夫", "背叛", "抛弃", "出轨", "替身"],
}

CONFLICT_KEYWORDS = {
    "身份反转": ["重生", "真假", "替身", "失忆", "归来", "身份"],
    "关系撕裂": ["离婚", "背叛", "婚", "前任", "误会", "宿敌"],
    "生死危机": ["死", "杀", "凶", "失踪", "逃", "追捕", "末日"],
    "权力博弈": ["太子", "夺嫡", "朝堂", "权臣", "继承", "豪门"],
    "限时任务": ["今晚", "三天", "七天", "倒计时", "最后", "必须"],
}

TITLE_FEATURE_KEYWORDS = {
    "时间/次数词": ["那年", "今晚", "最后", "第一次", "第二次", "重生后", "回到"],
    "关系词": ["前夫", "前妻", "白月光", "竹马", "丈夫", "妻子", "女儿", "母亲"],
    "身份词": ["千金", "少爷", "太子", "王妃", "总裁", "律师", "法医", "记者"],
    "事件词": ["失踪", "离婚", "死亡", "归来", "复仇", "告白", "追凶", "调包"],
}

PLATFORM_HINTS = {
    "general": "样本来自混合来源，结论更适合做通用启发，不适合下过强平台判断。",
    "fanqie": "更关注低门槛、强钩子、快反馈、强情绪回报。",
    "qidian": "更关注可持续连载、设定自洽、中长线成长与世界观稳定。",
    "qimao": "更关注直接卖点、快冲突、强反转、强进入感。",
}

STOPWORDS = {
    "我们", "他们", "你们", "一个", "一种", "什么", "怎么", "那个", "这个", "之后", "之前", "自己", "不是", "没有", "然后", "因为", "如果", "为了", "开始", "终于", "已经", "所有人", "故事", "小说",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="分析平台热榜快照文本")
    p.add_argument("--input", required=True, help="输入文件路径，每行一个标题或样本")
    p.add_argument("--platform", default="general", choices=["general", "fanqie", "qidian", "qimao"], help="平台类型")
    p.add_argument("--top", type=int, default=20, help="最多读取前 N 个样本")
    p.add_argument("--output", default="", help="可选：输出 markdown 报告文件")
    return p.parse_args()


def normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[\-•*]+\s*", "", line)
    line = re.sub(r"^(TOP)?\d+[\.、\s]+", "", line, flags=re.I)
    line = re.sub(r"^第?\d+名[:：\s]*", "", line)
    return line.strip()


def load_samples(path: Path, top_n: int) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cleaned = []
    for line in lines:
        text = normalize_line(line)
        if text:
            cleaned.append(text)
    return cleaned[:top_n]


def count_by_keywords(samples: list[str], mapping: dict[str, list[str]]) -> Counter:
    counter: Counter[str] = Counter()
    for sample in samples:
        matched_any = False
        for label, keywords in mapping.items():
            if any(keyword.lower() in sample.lower() for keyword in keywords):
                counter[label] += 1
                matched_any = True
        if not matched_any:
            counter["未明显归类"] += 1
    return counter


def extract_hot_terms(samples: list[str]) -> Counter:
    counter: Counter[str] = Counter()
    for sample in samples:
        for term in re.findall(r"[\u4e00-\u9fff]{2,6}", sample):
            if term in STOPWORDS:
                continue
            if len(term) == 2:
                counter[term] += 1
            elif len(term) <= 4:
                counter[term] += 1
    return counter


def top_lines(counter: Counter, limit: int = 5) -> list[str]:
    rows = []
    for label, count in counter.most_common(limit):
        rows.append(f"- {label}：{count}")
    return rows or ["- 暂无明显模式"]


def build_recommendations(genre_counter: Counter, conflict_counter: Counter, platform: str) -> list[str]:
    top_genres = [name for name, _ in genre_counter.most_common(3) if name != "未明显归类"]
    top_conflicts = [name for name, _ in conflict_counter.most_common(3) if name != "未明显归类"]
    if not top_genres:
        top_genres = ["现实", "悬疑"]
    if not top_conflicts:
        top_conflicts = ["身份反转", "生死危机"]

    suggestions = []
    for idx, genre in enumerate(top_genres[:3], start=1):
        conflict = top_conflicts[(idx - 1) % len(top_conflicts)]
        suggestions.append(f"### 方向 {idx}\n- 题材：{genre}\n- 适配平台：{platform}\n- 核心冲突：{conflict}\n- 建议：把卖点写进标题和前 3 章，先给异常事件，再给关系/身份变化。")
    return suggestions


def build_report(samples: list[str], platform: str) -> str:
    genre_counter = count_by_keywords(samples, GENRE_KEYWORDS)
    protagonist_counter = count_by_keywords(samples, PROTAGONIST_KEYWORDS)
    conflict_counter = count_by_keywords(samples, CONFLICT_KEYWORDS)
    feature_counter = count_by_keywords(samples, TITLE_FEATURE_KEYWORDS)
    hot_terms = extract_hot_terms(samples)
    confidence = "高" if len(samples) >= 15 else "中" if len(samples) >= 8 else "低"
    recommendation_blocks = build_recommendations(genre_counter, conflict_counter, platform)

    lines: list[str] = []
    lines.append("# 平台热榜快照分析报告")
    lines.append("")
    lines.append("## 1. 样本说明")
    lines.append(f"- 平台：{platform}")
    lines.append("- 榜单类型：热榜快照 / 标题列表")
    lines.append(f"- 样本量：{len(samples)}")
    lines.append(f"- 置信度：{confidence}")
    lines.append(f"- 平台提示：{PLATFORM_HINTS[platform]}")
    lines.append("")
    lines.append("## 2. 高频题材")
    lines.extend(top_lines(genre_counter))
    lines.append("")
    lines.append("## 3. 主角/人设模式")
    lines.extend(top_lines(protagonist_counter))
    lines.append("")
    lines.append("## 4. 核心冲突模式")
    lines.extend(top_lines(conflict_counter))
    lines.append("")
    lines.append("## 5. 标题表层模式")
    lines.extend(top_lines(feature_counter))
    lines.append("")
    lines.append("## 6. 高频词（启发式）")
    for word, count in hot_terms.most_common(10):
        lines.append(f"- {word}：{count}")
    if not hot_terms:
        lines.append("- 暂无明显高频词")
    lines.append("")
    lines.append("## 7. 可执行创作方向")
    lines.extend(recommendation_blocks)
    lines.append("")
    lines.append("## 8. 使用提醒")
    lines.append("- 这是启发式分析，适合辅助判断，不替代人工选题。")
    lines.append("- 最好结合榜单链接、简介、标签、评论区再做二次判断。")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"输入文件不存在: {input_path}")

    samples = load_samples(input_path, args.top)
    if not samples:
        raise SystemExit("输入文件没有可分析的样本")

    report = build_report(samples, args.platform)
    print(report)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"报告已写入: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
