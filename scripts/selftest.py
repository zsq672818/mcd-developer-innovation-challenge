#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py — 麦麦家长助手 · 回归自测

改阈值、改别名表、改营养快照之后先跑一遍：所有断言必须全绿，
否则不要拿去给家长报价。用例覆盖真实门店演练的组合、边界档位、
无数据单品、以及「全部超钠」的降级路径。

用法:
    python scripts/selftest.py        # 全部用例
    python scripts/selftest.py -v     # 打印每个用例的合计值
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from combo_evaluator import evaluate  # noqa: E402

CASES = [
    {
        "id": "7-10 鱼排堡开心乐园餐：三项全达标",
        "age": 8,
        "items": [("儿童鱼排堡", 1), ("迷你薯条", 1),
                  ("苹果片一袋(60g)", 1), ("纯牛奶(盒装)", 1)],
        "expect": {"totals": (536, 576, 24), "verdict": True,
                   "pass": {"kcal": True, "sodium": True, "protein": True}},
    },
    {
        "id": "7-10 汉堡开心乐园餐：三项全达标",
        "age": 8,
        "items": [("汉堡包", 1), ("迷你薯条", 1),
                  ("苹果片一袋(60g)", 1), ("纯牛奶(盒装)", 1)],
        "expect": {"totals": (515, 626, 22), "verdict": True,
                   "pass": {"kcal": True, "sodium": True, "protein": True}},
    },
    {
        "id": "7-10 麦乐鸡开心乐园餐：热量低于下限 → 不可推荐为常规",
        "age": 8,
        "items": [("麦乐鸡4块", 1), ("苹果片一袋(60g)", 1),
                  ("小杯玉米杯", 1), ("纯牛奶(盒装)", 1)],
        "expect": {"totals": (384, 411, 19), "verdict": False,
                   "pass": {"kcal": False, "sodium": True, "protein": True}},
    },
    {
        "id": "4-6 同一份麦乐鸡餐：热量落入 350-500 区间 → 达标",
        "age": 5,
        "items": [("麦乐鸡4块", 1), ("苹果片一袋(60g)", 1),
                  ("小杯玉米杯", 1), ("纯牛奶(盒装)", 1)],
        "expect": {"totals": (384, 411, 19), "verdict": True,
                   "pass": {"kcal": True, "sodium": True, "protein": True}},
    },
    {
        "id": "7-10 双层吉士汉堡+中薯条+可乐：钠与热量双超",
        "age": 9,
        "items": [("双层吉士汉堡", 1), ("中薯条", 1), ("可乐中杯", 1)],
        "expect": {"totals": (865, 1182, 31), "verdict": False,
                   "pass": {"kcal": False, "sodium": False, "protein": True},
                   "hint_contains": "钠超上限"},
    },
    {
        "id": "无数据单品必须报缺，不得估算",
        "age": 8,
        "items": [("汉堡包", 1), ("龙焰鸡腿堡", 1)],
        "expect": {"missing": ["龙焰鸡腿堡"], "verdict": False},
    },
    {
        "id": "别名表：苹果片一袋(60g) 应折算为「苹果片」并声明假设",
        "age": 8,
        "items": [("苹果片一袋(60g)", 1)],
        "expect": {"assumed": ["苹果片一袋(60g)"], "totals_kcal": 32},
    },
    {
        "id": "3 岁借用 4-6 岁表并附儿保提示",
        "age": 3,
        "items": [("汉堡包", 1), ("纯牛奶(盒装)", 1)],
        "expect": {"age_note": True, "bucket": "4-6"},
    },
]


def run(verbose=False):
    failed = 0
    for case in CASES:
        res = evaluate(case["age"], case["items"], gender="男", restrict="不吃辣")
        errs = []
        exp = case["expect"]

        if "totals" in exp:
            got = (res["totals"]["kcal"], res["totals"]["sodium"], res["totals"]["protein"])
            if got != exp["totals"]:
                errs.append(f"合计期望 {exp['totals']} 实际 {got}")
        if "totals_kcal" in exp and res["totals"]["kcal"] != exp["totals_kcal"]:
            errs.append(f"热量期望 {exp['totals_kcal']} 实际 {res['totals']['kcal']}")
        if "verdict" in exp and res["verdict"] != exp["verdict"]:
            errs.append(f"结论期望 {exp['verdict']} 实际 {res['verdict']}")
        for k, v in exp.get("pass", {}).items():
            if res["checks"][k]["pass"] != v:
                errs.append(f"{k} 判定期望 {v} 实际 {res['checks'][k]['pass']}")
        if "missing" in exp and res["missing"] != exp["missing"]:
            errs.append(f"缺失单品期望 {exp['missing']} 实际 {res['missing']}")
        if "assumed" in exp:
            got = [c["name"] for c in res["components"] if c["assumed"]]
            if got != exp["assumed"]:
                errs.append(f"假设声明期望 {exp['assumed']} 实际 {got}")
        if "age_note" in exp and bool(res["age_note"]) != exp["age_note"]:
            errs.append("年龄提示缺失")
        if "bucket" in exp and res["bucket"] != exp["bucket"]:
            errs.append(f"档位期望 {exp['bucket']} 实际 {res['bucket']}")
        if "hint_contains" in exp and not any(exp["hint_contains"] in h for h in res["hints"]):
            errs.append(f"提示中缺少「{exp['hint_contains']}」")

        status = "PASS" if not errs else "FAIL"
        if errs:
            failed += 1
        print(f"[{status}] {case['id']}")
        if verbose or errs:
            t = res["totals"]
            print(f"        {t['kcal']} kcal / {t['sodium']} mg / {t['protein']} g "
                  f"→ {'达标' if res['verdict'] else '不达标'}")
        for e in errs:
            print(f"        ↳ {e}")

    print("-" * 56)
    print(f"{len(CASES) - failed}/{len(CASES)} 通过")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run(verbose="-v" in sys.argv))
