#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""combo_evaluator.py — 麦麦家长助手 · 组合营养校验器

对一个儿童套餐组合做确定性核算：营养求和、年龄硬约束校验、占每日建议百分比、
开心度检查、诚实降级提示。目的只有一个——把「算数」从模型手里拿走，
避免口算错误，也让家长可以复现每一个数字。

用法:
    python combo_evaluator.py --age 8 \
        --items "汉堡包 x1, 迷你薯条 x1, 苹果片一袋(60g) x1, 纯牛奶(盒装) x1" \
        --happy "薯条,玩具" --price 23.5 --coupon-price 23.5 --gender 男 --restrict 不吃辣

    python combo_evaluator.py --age 8 --json --items "麦乐鸡4块 x1, 纯牛奶(盒装) x1"
    python combo_evaluator.py --age 4 --items-file items.json

参数:
    --age          孩子年龄 3-12（必填；3 岁按 4-6 岁表执行并提示咨询儿保医生）
    --items        组件列表，"品名 x数量"，逗号分隔，数量缺省为 1
    --items-file   组件 JSON 文件（优先于 --items），如 [{"name":"麦乐鸡4块","qty":1}]
    --happy        实际开心元素，逗号分隔（缺省按品名自动探测）
    --price        组合原价，单位元
    --coupon-price 券后实付价，单位元（无券时与原价相同，可直接省略）
    --gender       性别（仅记录）
    --restrict     忌口/过敏（仅记录与提示）
    --nutrition    营养数据 JSON（默认 references/nutrition-data.json）
    --json         输出机器可读 JSON（供卡片渲染/批量评估），不打印人读报告

退出码: 0 = 正常输出（含不达标判定）；1 = 用法/数据错误
"""
import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------- 常量
AGE_TABLE = {
    "4-6":   {"kcal": (350, 500), "sodium_max": 550, "protein_min": 12},
    "7-10":  {"kcal": (450, 600), "sodium_max": 700, "protein_min": 15},
    "11-12": {"kcal": (500, 700), "sodium_max": 850, "protein_min": 18},
}
DAILY_REF = {
    "4-6":   {"kcal": 1400, "sodium": 900,  "protein": 25, "calcium": 800},
    "7-10":  {"kcal": 1800, "sodium": 1200, "protein": 30, "calcium": 1000},
    "11-12": {"kcal": 2000, "sodium": 1400, "protein": 40, "calcium": 1000},
}
# 菜单名 → 营养库默认对应（歧义时取此默认值，并在输出中显式声明假设）
ALIASES = {
    "薯条": "中薯条", "玉米杯": "大杯玉米杯", "派": "菠萝派", "新地": "朱古力新地",
    "麦乐鸡": "麦乐鸡4块", "纯牛奶": "纯牛奶（盒装）", "牛奶": "纯牛奶（盒装）",
    "可乐": "可乐中杯", "雪碧": "雪碧中杯", "怡泉+C": "中杯怡泉+C",
    "阳光柠檬红茶": "阳光柠檬红茶中杯", "美式": "热美式中杯", "麦咖啡美式": "热美式中杯",
    "卡布奇诺": "卡布奇诺中杯", "奶铁": "冰奶铁中杯", "麦咖啡奶铁": "冰奶铁中杯",
    "燕麦奶铁": "冰燕麦奶铁中杯", "麦麦脆汁鸡1块": "麦麦脆汁鸡-带骨里脊",
    "苹果片一袋(60g)": "苹果片", "苹果片一袋（60g）": "苹果片", "苹果片": "苹果片",
    "鱼排堡": "儿童鱼排堡", "儿童鱼排堡": "儿童鱼排堡",
    "麦辣鸡翅": "麦辣鸡翅-2块", "麦辣鸡腿汉堡": "麦辣鸡腿汉堡",
    "纯牛奶(盒装)": "纯牛奶（盒装）", "100% 苹果汁(盒装)": "100%苹果汁",
    "100%苹果汁(盒装)": "100%苹果汁", "100%苹果汁（盒装）": "100%苹果汁",
    "鲜萃咖啡": "大杯鲜萃咖啡", "【美汁源】黄金橙橙": "【美汁源】“黄金橙橙”",
    "那么大鸡排（椒盐风味）": "那么大鸡排", "麦乐鸡块": "麦乐鸡4块",
    "麦乐鸡-4块": "麦乐鸡4块", "麦乐鸡4块": "麦乐鸡4块",
}
# 开心元素关键词（自动探测用）
HAPPY_PATTERNS = [
    ("薯条", ["薯条"]),
    ("甜品", ["新地", "派", "麦旋风", "冰淇淋", "雪糕", "圆筒", "雪冰"]),
    ("开心乐园餐玩具", ["玩具"]),
    ("麦乐鸡", ["麦乐鸡"]),
]
KCAL_FILLERS = "迷你薯条(+106 kcal)、麦乐鸡4块(+170 kcal)、纯牛奶盒装(+129 kcal)"
PROTEIN_FILLERS = "麦乐鸡4块(+10 g)、板烧鸡腿堡(+23 g)、纯牛奶盒装(+7 g)"

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NUTRITION = SKILL_ROOT / "references" / "nutrition-data.json"


# ---------------------------------------------------------------- 工具函数
def age_bucket(age: int):
    if age == 3:
        return "4-6", "3 岁借用 4-6 岁表：幼儿个体差异大，建议咨询儿保医生"
    if 4 <= age <= 6:
        return "4-6", None
    if 7 <= age <= 10:
        return "7-10", None
    if 11 <= age <= 12:
        return "11-12", None
    return None, f"年龄 {age} 超出 3-12 岁服务范围"


def load_nutrition(path: Path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data}


def match_name(raw: str, table: dict, assumptions: list):
    """精确匹配 → 别名表 → 无数据。

    刻意不做模糊匹配：静默把 A 产品的营养数据安到 B 产品上，
    是儿童营养工具最危险的失败模式。未知名称必须报告「无数据」。
    """
    name = raw.strip()
    if name in table:
        return name
    if name in ALIASES and ALIASES[name] in table:
        assumptions.append(
            f"「{name}」按「{ALIASES[name]}」计（歧义默认值，建议向家长确认规格）")
        return ALIASES[name]
    return None


def parse_items(s: str):
    items = []
    for part in s.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        matched = False
        for sep in (" x", " X", "×", "*"):
            if sep in part:
                name, qty = part.rsplit(sep, 1)
                try:
                    items.append((name.strip(), int(qty.strip())))
                except ValueError:
                    items.append((part, 1))
                matched = True
                break
        if not matched:
            items.append((part, 1))
    return items


def detect_happy(names):
    return [el for el, pats in HAPPY_PATTERNS
            if any(p in n for n in names for p in pats)]


def pct(part, whole):
    return round(part / whole * 100) if whole else 0


# ---------------------------------------------------------------- 核心评估
def evaluate(age, items, happy=None, price=None, coupon_price=None,
             gender=None, restrict=None, nutrition_path=None):
    """对单个组合做评估，返回 dict（人读报告与 JSON 共用同一份结果）。

    items: [(name, qty), ...] 或 [{"name":..., "qty":...}, ...]
    """
    bucket, note = age_bucket(int(age))
    if bucket is None:
        raise ValueError(note)

    table = load_nutrition(Path(nutrition_path or DEFAULT_NUTRITION))
    norm = []
    for it in items:
        if isinstance(it, dict):
            norm.append((str(it["name"]), int(it.get("qty", 1))))
        else:
            norm.append((str(it[0]), int(it[1])))

    assumptions, missing, components = [], [], []
    totals = {"kcal": 0, "sodium": 0, "protein": 0, "calcium": 0}
    for name, qty in norm:
        matched = match_name(name, table, assumptions)
        if matched is None:
            missing.append(name)
            continue
        d = table[matched]
        for k in totals:
            totals[k] += d[k] * qty
        components.append({
            "name": name, "matched": matched, "qty": qty,
            "assumed": matched != name,
            "kcal": d["kcal"], "sodium": d["sodium"],
            "protein": d["protein"], "calcium": d["calcium"],
        })

    c, r = AGE_TABLE[bucket], DAILY_REF[bucket]
    lo, hi = c["kcal"]
    checks = {
        "kcal": {"value": totals["kcal"], "min": lo, "max": hi,
                 "pass": lo <= totals["kcal"] <= hi},
        "sodium": {"value": totals["sodium"], "max": c["sodium_max"],
                   "pass": totals["sodium"] <= c["sodium_max"]},
        "protein": {"value": totals["protein"], "min": c["protein_min"],
                    "pass": totals["protein"] >= c["protein_min"]},
    }
    daily = {k: pct(totals[k], r[k if k != "kcal" else "kcal"]) for k in totals}

    if happy is None:
        happy = detect_happy([x["name"] for x in components])
    elif isinstance(happy, str):
        happy = [h.strip() for h in happy.replace("，", ",").split(",") if h.strip()]

    hints = []
    if not checks["sodium"]["pass"]:
        hints.append(f"钠超上限 {totals['sodium'] - c['sodium_max']} mg："
                     "建议酱料减半/去酱、含糖饮料换水或牛奶、大份换小份，或两人分享")
    if totals["kcal"] < lo:
        hints.append(f"热量低于下限 {lo - totals['kcal']} kcal：可加 {KCAL_FILLERS}")
    if totals["kcal"] > hi:
        hints.append(f"热量超上限 {totals['kcal'] - hi} kcal：去掉小食或换迷你份")
    if not checks["protein"]["pass"]:
        hints.append(f"蛋白质低于下限 {c['protein_min'] - totals['protein']} g："
                     f"可换/加 {PROTEIN_FILLERS}")
    for a in assumptions:
        hints.append(f"假设声明：{a}")
    if missing:
        hints.append(f"无营养数据单品：{'、'.join(missing)}（不纳入合计，请以柜台信息为准）")
    if restrict and any(k in str(restrict) for k in ("花生", "坚果", "过敏", "不耐", "乳", "海鲜")):
        hints.append("过敏提示：麦当劳产品可能存在交叉污染（共用生产线/烹炸油），"
                     "如有过敏史请务必咨询店员确认后再点")

    verdict = all(ch["pass"] for ch in checks.values()) and bool(happy)
    return {
        "age": int(age), "bucket": bucket, "age_note": note,
        "gender": gender, "restrict": restrict,
        "components": components, "missing": missing,
        "totals": totals, "checks": checks, "daily_pct": daily,
        "happy": happy, "happy_ok": bool(happy),
        "hints": hints, "verdict": verdict,
        "price": price, "coupon_price": coupon_price,
    }


# ---------------------------------------------------------------- 人读报告
def render(res):
    c = AGE_TABLE[res["bucket"]]
    lines = ["=" * 60]
    head = f"麦麦家长助手 · 组合营养核算（{res['age']} 岁 · {res['bucket']} 岁段"
    if res["gender"]:
        head += f" · {res['gender']}"
    lines.append(head + "）")
    if res["restrict"]:
        lines.append(f"忌口/过敏记录：{res['restrict']}")
    lines.append("=" * 60)
    if res["age_note"]:
        lines.append(f"⚠ {res['age_note']}")

    lines.append("\n【组件明细】")
    for x in res["components"]:
        suffix = f"（按「{x['matched']}」计）" if x["assumed"] else ""
        lines.append(f"  - {x['name']}{suffix} x{x['qty']}: {x['kcal']} kcal / "
                     f"钠 {x['sodium']} mg / 蛋白质 {x['protein']} g / 钙 {x['calcium']} mg")
    if res["missing"]:
        lines.append(f"  ⚠ 无营养数据单品：{'、'.join(res['missing'])}（不纳入合计）")

    t = res["totals"]
    lines.append(f"\n【合计】热量 {t['kcal']} kcal · 钠 {t['sodium']} mg · "
                 f"蛋白质 {t['protein']} g · 钙 {t['calcium']} mg")

    lines.append("\n【硬约束校验】")
    ck = res["checks"]
    lines.append(f"  [{'PASS' if ck['kcal']['pass'] else 'FAIL'}] 热量 {ck['kcal']['value']} kcal"
                 f"（要求 {ck['kcal']['min']}-{ck['kcal']['max']}）")
    lines.append(f"  [{'PASS' if ck['sodium']['pass'] else 'FAIL'}] 钠 {ck['sodium']['value']} mg"
                 f"（上限 {ck['sodium']['max']} mg）")
    lines.append(f"  [{'PASS' if ck['protein']['pass'] else 'FAIL'}] 蛋白质 {ck['protein']['value']} g"
                 f"（下限 {ck['protein']['min']} g）")

    d = res["daily_pct"]
    lines.append("\n【占每日建议百分比】")
    lines.append(f"  热量 {d['kcal']}% · 钠 {d['sodium']}% · 蛋白质 {d['protein']}% · 钙 {d['calcium']}%")
    lines.append("  （参考值：中国居民膳食营养素参考摄入量 + WHO 儿童钠建议折算，仅供参考，非医学建议）")

    lines.append("\n【开心度】")
    lines.append(f"  命中开心元素：{'、'.join(res['happy']) if res['happy'] else '无'}"
                 f"（{'满足' if res['happy'] else '不满足'}软约束：至少 1 项薯条/甜品/玩具/麦乐鸡）")

    lines.append("\n【诚实提示】")
    lines.extend([f"  - {h}" for h in res["hints"]] or ["  - 无"])

    lines.append(f"\n【结论】{'✅ 营养达标且孩子开心，可推荐' if res['verdict'] else '⚠️ 存在不达标项，按诚实降级策略处理'}")
    if res["price"] is not None:
        lines.append(f"【价格】原价 ¥{res['price']:.2f}")
    if res["coupon_price"] is not None:
        lines.append(f"【券后】实付 ¥{res['coupon_price']:.2f}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="麦麦家长助手 · 组合营养校验器")
    ap.add_argument("--age", type=int, required=True, help="孩子年龄 3-12")
    ap.add_argument("--items", help='组件列表，如 "汉堡包 x1, 迷你薯条 x1"')
    ap.add_argument("--items-file", help="组件 JSON 文件")
    ap.add_argument("--happy", help="开心元素，逗号分隔（缺省自动探测）")
    ap.add_argument("--price", type=float, help="组合原价（元）")
    ap.add_argument("--coupon-price", dest="coupon_price", type=float, help="券后价（元）")
    ap.add_argument("--gender", help="性别（仅记录）")
    ap.add_argument("--restrict", help="忌口/过敏（仅记录与提示）")
    ap.add_argument("--nutrition", default=str(DEFAULT_NUTRITION), help="营养数据 JSON")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非人读报告")
    args = ap.parse_args()

    if args.items_file:
        with open(args.items_file, encoding="utf-8") as f:
            items = json.load(f)
    elif args.items:
        items = parse_items(args.items)
    else:
        print("[错误] 必须提供 --items 或 --items-file")
        return 1

    try:
        res = evaluate(args.age, items, happy=args.happy, price=args.price,
                       coupon_price=args.coupon_price, gender=args.gender,
                       restrict=args.restrict, nutrition_path=args.nutrition)
    except ValueError as e:
        print(f"[错误] {e}")
        return 1

    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
