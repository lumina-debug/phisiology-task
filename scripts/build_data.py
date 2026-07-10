#!/usr/bin/env python3
"""exams.json / flashcards.json をブラウザがfile://で読める data.js に変換する。"""
import json, os
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
exams = json.load(open(os.path.join(APP, "exams.json"), encoding="utf-8"))
cards = json.load(open(os.path.join(APP, "flashcards.json"), encoding="utf-8"))
with open(os.path.join(APP, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.EXAM_DATA=")
    json.dump(exams, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\nwindow.CARD_DATA=")
    json.dump(cards, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("data.js:", os.path.getsize(os.path.join(APP, "data.js")) // 1024, "KB")
