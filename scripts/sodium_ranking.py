#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sodium_ranking.py — 麦麦家长助手 · 菜单单品低钠排行榜

把 query-meals 拉到的门店菜单与 list-nutrition-foods 的营养数据关联，
按钠含量从低到高排序输出表格（品名/热量/钠/蛋白质/价格）。

用法:
    python sodium_ranking.py --menu meals.json [--top 20] [--out table.md]
    python sodium_ranking.py --menu meals.json --nutrition nutrition.json

参数:
    --menu        query-meals 的原始响应 JSON 文件（自动识别 data.meals 映射表）
    --nutrition   营养数据。支持两种格式：
                   (a) 技能内置 references/nutrition-data.json（默认）
                   (b) list-nutrition-foods 原始响应（JSON 或 "[160]{...}:" 自定义文本）
    --top         输出前 N 名（默认 20）
    --out         输出 Markdown 文件（缺省打印到 stdout）

注意:
    - query-meals 的 currentPrice 单位是【元】，直接展示，不要除以 100
    - calculate-price 的返回单位才是【分】，展示时 ÷100
    - 未匹配到营养数据的单品不参与排名，单独列出，严禁估算
"""
import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NUTRITION = SKILL_ROOT / "references" / "nutrition-data.json"

# 菜单名 → 营养库默认对应（歧义默认值，输出中显式声明）
ALIASES = {
    "薯条": "中薯条", "玉米杯": "大杯玉米杯", "派": "菠萝派", "新地": "朱古力新地",
    "麦乐鸡": "麦乐鸡4块", "纯牛奶": "纯牛奶（盒装）", "牛奶": "纯牛奶（盒装）",
    "可乐": "可乐中杯", "雪碧": "雪碧中杯", "怡泉+C": "中杯怡泉+C",
    "阳光柠檬红茶": "阳光柠檬红茶中杯", "美式": "热美式中杯", "麦咖啡美式": "热美式中杯",
    "卡布奇诺": "卡布奇诺中杯", "奶铁": "冰奶铁中杯", "麦咖啡奶铁": "冰奶铁中杯",
    "燕麦奶铁": "冰燕麦奶铁中杯", "麦麦脆汁鸡1块": "麦麦脆汁鸡-带骨里脊",
    "苹果片一袋(60g)": "苹果片", "苹果片一袋（60g）": "苹果片", "鱼排堡": "儿童鱼排堡",
    "麦辣鸡翅": "麦辣鸡翅-2块", "麦辣鸡腿汉堡": "麦辣鸡腿汉堡",
    "纯牛奶(盒装)": "纯牛奶（盒装）", "100% 苹果汁(盒装)": "100%苹果汁",
    "100%苹果汁(盒装)": "100%苹果汁", "100%苹果汁（盒装）": "100%苹果汁",
    "鲜萃咖啡": "大杯鲜萃咖啡", "【美汁源】黄金橙橙": "【美汁源】“黄金橙橙”",
    "那么大鸡排（椒盐风味）": "那么大鸡排", "麦乐鸡块": "麦乐鸡4块",
}


def parse_custom_nutrition(text: str):
    """解析 list-nutrition-foods 的自定义文本格式:
    [160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:
      猪柳麦满分,null,1288,308,16,16,24,781,213
      ...
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("[") or "{" in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9 or parts[0] in ("productName",):
            continue

        def num(x):
            try:
                return float(x)
            except ValueError:
                return 0.0

        rows.append({
            "name": parts[0],
            "kcal": num(parts[3]), "protein": num(parts[4]),
            "fat": num(parts[5]), "carb": num(parts[6]),
            "sodium": num(parts[7]), "calcium": num(parts[8]),
        })
    return rows


def load_nutrition(path: Path):
    raw = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return parse_custom_nutrition(raw)
    if isinstance(obj, dict) and isinstance(obj.get("data"), str):
        return parse_custom_nutrition(obj["data"])
    if isinstance(obj, dict) and isinstance(obj.get("data"), list):
        return obj["data"]
    if isinstance(obj, list):
        return obj
    return []


def load_menu(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    data = obj.get("data", obj)
    meals = data.get("meals", {}) if isinstance(data, dict) else {}
    out = []
    for code, m in meals.items():
        name = m.get("name")
        price = m.get("currentPrice")
        if not name:
            continue
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = None
        out.append({"code": code, "name": name, "price": price})
    return out


def main():
    ap = argparse.ArgumentParser(description="麦麦家长助手 · 菜单单品低钠排行榜")
    ap.add_argument("--menu", required=True, help="query-meals 原始响应 JSON")
    ap.add_argument("--nutrition", default=str(DEFAULT_NUTRITION), help="营养数据")
    ap.add_argument("--top", type=int, default=20, help="输出前 N 名")
    ap.add_argument("--out", help="输出 Markdown 文件（缺省打印 stdout）")
    args = ap.parse_args()

    menu = load_menu(Path(args.menu))
    nutrition = load_nutrition(Path(args.nutrition))
    table = {}
    for item in nutrition:
        table[item["name"]] = item

    matched, unmatched, assumptions = [], [], []
    for m in menu:
        name = m["name"]
        if name in table:
            matched.append((name, table[name], m["price"], False))
        elif name in ALIASES and ALIASES[name] in table:
            matched.append((name, table[ALIASES[name]], m["price"], True))
            assumptions.append(f"「{name}」按「{ALIASES[name]}」计")
        else:
            # 刻意不做模糊匹配：防止把 A 产品营养数据静默安到 B 产品上
            unmatched.append(name)

    matched.sort(key=lambda x: (x[1]["sodium"], x[1]["kcal"]))

    lines = []
    lines.append("# 门店菜单单品 · 低钠排行榜")
    lines.append("")
    lines.append(f"- 排名口径：按钠含量从低到高（同钠按热量升序），取前 {args.top} 名")
    lines.append("- 数据来源：query-meals（菜单/价格，单位元） + list-nutrition-foods（营养）")
    lines.append("- 注意：calculate-price 返回的价格单位才是「分」；本表价格直接来自菜单，单位为元")
    lines.append("")
    lines.append("| 排名 | 品名 | 热量 (kcal) | 钠 (mg) | 蛋白质 (g) | 价格 (¥) |")
    lines.append("|---|---|---|---|---|---|")
    for i, (name, d, price, assumed) in enumerate(matched[: args.top], 1):
        price_s = f"{price:.1f}" if price is not None else "—"
        flag = " *" if assumed else ""
        lines.append(f"| {i} | {name}{flag} | {d['kcal']:.0f} | {d['sodium']:.0f} "
                     f"| {d['protein']:.0f} | {price_s} |")
    if assumptions:
        lines.append("")
        lines.append("带 * 项为歧义规格的默认取值：" + "；".join(assumptions) + "。")
    if unmatched:
        lines.append("")
        lines.append("## 无营养数据单品（不参与排名，严禁估算）")
        lines.append("")
        lines.append("、".join(unmatched))
    lines.append("")
    lines.append(f"共匹配 {len(matched)} 项，无数据 {len(unmatched)} 项。")

    text = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
