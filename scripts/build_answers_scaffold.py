#!/usr/bin/env python3
"""ユニーク設問ごとの解答スカフォールドを生成/更新する。
- 各問題を正規化キー(ck)で集約し、代表問題文・出題年度・テーマを付与
- 既存 docs/answers.json の a/e は保持してマージ（追記式）
- テーマ頻度順→設問文順に並べて出力（頻出テーマから解答を書きやすく）
"""
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
exams = json.load(open(os.path.join(DOCS, "exams.json"), encoding="utf-8"))
ans_path = os.path.join(DOCS, "answers.json")
existing = {}
if os.path.exists(ans_path):
    existing = json.load(open(ans_path, encoding="utf-8"))

def ck(text):
    t = re.sub(r'[\s　（）()0-9０-９().、,．・:：;；]+', '', text)
    return t[:60]

groups = {}
for e in exams["exams"]:
    for q in e["questions"]:
        text = " ".join(s["v"] for s in q["segments"] if s["t"] == "text")
        key = ck(text)
        g = groups.setdefault(key, {"q": text, "topics": q.get("topics", ["その他"]),
                                    "years": [], "len": len(text)})
        g["years"].append(e["year"])
        if len(text) > g["len"]:
            g["q"] = text; g["len"] = len(text)  # 最長の問題文を代表に

# テーマ頻度
tf = {}
for g in groups.values():
    for t in g["topics"]:
        tf[t] = tf.get(t, 0) + len(g["years"])

def sortkey(item):
    k, g = item
    top = g["topics"][0]
    return (-tf.get(top, 0), top, -len(g["years"]), g["q"][:30])

out = {}
for k, g in sorted(groups.items(), key=sortkey):
    prev = existing.get(k, {})
    out[k] = {
        "q": g["q"],
        "topics": g["topics"],
        "years": sorted(set(g["years"])),
        "a": prev.get("a", ""),
        "e": prev.get("e", ""),
    }
json.dump(out, open(ans_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
filled = sum(1 for v in out.values() if v["a"])
print(f"answers.json: {len(out)}件 (解答済み {filled}件)")
print("テーマ頻度順:")
for t, n in sorted(tf.items(), key=lambda x: -x[1]):
    print(f"  {n:3d}  {t}")
