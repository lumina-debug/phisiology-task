#!/usr/bin/env python3
"""exams.json / flashcards.json / answers.json をブラウザがfile://で読める data.js に変換する。
answers.json（正規化キーで集約した解答）を各設問に紐づける。"""
import json, os, re
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def ck(text):
    t = re.sub(r'[\s　（）()0-9０-９().、,．・:：;；]+', '', text)
    return t[:60]

exams = json.load(open(os.path.join(APP, "exams.json"), encoding="utf-8"))
cards = json.load(open(os.path.join(APP, "flashcards.json"), encoding="utf-8"))
answers = {}
ap = os.path.join(APP, "answers.json")
if os.path.exists(ap):
    answers = json.load(open(ap, encoding="utf-8"))

# 各設問に解答(a)・解説(e)を紐づけ
filled = 0
for e in exams["exams"]:
    for q in e["questions"]:
        text = " ".join(s["v"] for s in q["segments"] if s["t"] == "text")
        a = answers.get(ck(text))
        if a and a.get("a"):
            q["a"] = a["a"]
            q["e"] = a.get("e", "")
            filled += 1

with open(os.path.join(APP, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.EXAM_DATA=")
    json.dump(exams, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\nwindow.CARD_DATA=")
    json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("data.js:", os.path.getsize(os.path.join(APP, "data.js")) // 1024, "KB /",
      "解答紐づけ", filled, "問")
