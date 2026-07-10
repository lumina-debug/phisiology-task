#!/usr/bin/env python3
"""過去問HTMLを構造化JSONに変換する。
各年度のファイルを [問題N] 単位に分割し、テキスト行と画像(データURI)を保持する。
"""
import re, html, json, glob, os

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SRC_DIR, "app", "exams.json")

# トピック分類キーワード（頻出テーマ）
TOPICS = {
    "膜輸送・膜タンパク質": ["促進輸送", "能動輸送", "受動輸送", "チャネル", "担体", "輸送タンパク", "共輸送", "拡散", "エンドサイト", "エキソサイト", "ATPase", "ナトリウムポンプ", "Na,K", "Na+/K+", "ポンプ", "脂質二重", "二重層", "シンポーター", "トランスポーター"],
    "浸透圧・体液": ["モル濃度", "オスモル", "浸透圧", "生食", "赤血球", "膨張", "収縮", "アルブミン", "体液", "細胞外液", "細胞内液"],
    "膜電位・活動電位": ["静止膜電位", "活動電位", "平衡電位", "脱分極", "過分極", "閾値", "gNa", "gK", "Naチャネル", "Kチャネル", "不活性化", "ネルンスト", "膜電位", "跳躍伝導", "有髄", "髄鞘", "ランビエ"],
    "シナプス・神経伝達": ["シナプス", "神経伝達物質", "伝達物質", "小胞", "興奮性", "抑制性", "EPSP", "IPSP", "再取り込み", "加重"],
    "細胞間シグナル・情報伝達": ["細胞間化学シグナル", "細胞間シグナル", "シグナル分子", "化学シグナル", "受容機構", "オートクリン", "パラクリン", "ジャクスタクリン", "ギャップ結合", "セカンドメッセンジャー", "cAMP", "プロテインキナーゼ", "シグナル増幅"],
    "筋・骨格筋代謝": ["グリコーゲンがアドレナリン", "アドレナリンの作用によって分解", "骨格筋", "精細管", "セルトリ", "ライディッヒ", "アンドロゲンの骨格筋"],
    "内分泌総論・下垂体": ["視床下部", "下垂体", "成長ホルモン", "GH", "TSH", "ACTH", "フィードバック", "標的組織", "末梢軸", "放出ホルモン", "プロラクチン", "オキシトシン", "後葉", "射乳"],
    "甲状腺": ["甲状腺", "サイログロブリン", "バセドウ", "T3", "T4", "ヨウ素", "ヨード", "TRH", "クレチン"],
    "副腎": ["副腎", "アドレナリン", "コルチゾール", "Cushing", "クッシング", "アルドステロン", "髄質", "皮質", "カテコールアミン", "糖質コルチコイド", "グルココルチコイド", "コルチコイド"],
    "膵臓・糖代謝・糖尿病": ["インスリン", "グルカゴン", "糖尿病", "ケトアシドーシス", "血糖", "膵", "低血糖", "耐糖能", "GLP", "インクレチン", "合併症", "グルコース", "糖新生", "グリコーゲン", "貯蔵", "空腹時", "食後", "肝細胞"],
    "カルシウム代謝": ["カルシウム", "副甲状腺", "PTH", "ビタミンD", "カルシトニン", "骨芽", "破骨", "骨端"],
    "生殖・性周期": ["卵巣", "黄体", "月経", "エストロゲン", "プロゲステロン", "排卵", "胎盤", "妊娠", "LH", "FSH", "精子", "テストステロン", "性周期", "hCG", "絨毛性", "ゴナドトロピン", "ソマトマンモトロピン", "閉経", "更年期"],
    "腎臓・尿濃縮": ["GFR", "糸球体", "濾過", "ヘンレ", "係蹄", "尿細管", "直血管", "対向流", "クリアランス", "イヌリン", "腎", "再吸収", "近位", "遠位", "レニン", "アンギオテンシン", "アンジオテンシン"],
    "水・電解質・ADH": ["ADH", "抗利尿", "バソプレシン", "浸透圧受容", "集合管", "水の再吸収", "口渇"],
    "酸塩基平衡": ["酸塩基", "アシドーシス", "アルカローシス", "HCO3", "揮発性酸", "pH", "代償", "呼吸性", "代謝性", "緩衝"],
    "呼吸・代謝": ["呼吸商", "エネルギー源", "RQ", "酸素消費", "換気", "呼吸"],
    "循環・ショック・浮腫": ["循環ショック", "ショック", "浮腫", "血圧", "心拍出", "循環血液量"],
}

def classify(text):
    scores = {}
    for topic, kws in TOPICS.items():
        s = sum(text.count(k) for k in kws)
        if s:
            scores[topic] = s
    if not scores:
        return ["その他"]
    mx = max(scores.values())
    # 最大スコア及びその近傍を採用（最大2トピック）
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    out = [ranked[0][0]]
    for t, s in ranked[1:]:
        if s >= max(2, mx * 0.6) and len(out) < 2:
            out.append(t)
    return out

def clean_block(block_html):
    """1問題分のHTMLからテキスト行と画像を抽出"""
    segs = []
    # 画像を占位トークンに置換して回収
    imgs = []
    def imgrepl(m):
        src = re.search(r'src="([^"]+)"', m.group(0))
        if src and src.group(1).startswith("data:"):
            imgs.append(src.group(1))
            return f"\x00IMG{len(imgs)-1}\x00"
        return " "
    block_html = re.sub(r'<img[^>]*>', imgrepl, block_html)
    # 改行系タグを改行に
    block_html = re.sub(r'<\s*(br|/p|/li|/div|/tr|/h\d)\s*/?>', '\n', block_html, flags=re.I)
    block_html = re.sub(r'<[^>]+>', ' ', block_html)
    text = html.unescape(block_html)
    text = text.replace('　', ' ')
    lines = []
    for raw in text.split('\n'):
        line = re.sub(r'[ \t]+', ' ', raw).strip()
        if not line:
            continue
        lines.append(line)
    # 画像トークンを行として展開
    out = []
    for line in lines:
        parts = re.split(r'(\x00IMG\d+\x00)', line)
        buf = ""
        for p in parts:
            m = re.match(r'\x00IMG(\d+)\x00', p)
            if m:
                if buf.strip():
                    out.append({"t": "text", "v": buf.strip()})
                    buf = ""
                out.append({"t": "img", "v": imgs[int(m.group(1))]})
            else:
                buf += p
        if buf.strip():
            out.append({"t": "text", "v": buf.strip()})
    return out

from html.parser import HTMLParser

NUM_STYLES = [
    lambda i: str(i + 1),                      # 1,2,3 (問題番号)
    lambda i: f"({i + 1})",                    # (1),(2)
    lambda i: f"({chr(ord('a') + i)})",       # (a),(b)
    lambda i: f"({chr(ord('a') + i)})",
]

class ListExamParser(HTMLParser):
    """最上位<ol>直下の<li>を問題として抽出。ネストした番号付け・画像を保持。"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ol_depth = 0
        self.counters = []          # 各olレベルの現在カウンタ
        self.questions = []         # [{"num":.., "segments":[...]}]
        self.cur_segs = None        # 現在の問題のsegmentリスト
        self.buf = ""
        self.pending_prefix = None  # 次のテキストに付与する番号プレフィクス

    def _flush(self):
        if self.cur_segs is None:
            return
        txt = re.sub(r'[ \t]+', ' ', self.buf).strip()
        if self.pending_prefix and txt:
            txt = f"{self.pending_prefix} {txt}"
        elif self.pending_prefix and not txt:
            txt = self.pending_prefix
        if txt:
            self.cur_segs.append({"t": "text", "v": txt})
        self.buf = ""
        self.pending_prefix = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "ol":
            self._flush()
            self.ol_depth += 1
            self.counters.append(0)
        elif tag == "li":
            self._flush()
            lvl = self.ol_depth - 1
            if lvl < 0:
                return
            idx = self.counters[lvl]
            self.counters[lvl] += 1
            if self.ol_depth == 1:
                # 新しい問題
                self.cur_segs = []
                self.questions.append({"num": str(idx + 1), "segments": self.cur_segs})
            else:
                style = NUM_STYLES[min(lvl, len(NUM_STYLES) - 1)]
                self.pending_prefix = style(idx)
        elif tag in ("br", "p", "div"):
            self._flush()
        elif tag == "img":
            d = dict(attrs)
            src = d.get("src", "")
            if src.startswith("data:") and self.cur_segs is not None:
                self._flush()
                self.cur_segs.append({"t": "img", "v": src})

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "ol":
            self._flush()
            if self.ol_depth > 0:
                self.ol_depth -= 1
                self.counters.pop()
        elif tag in ("li", "p", "div"):
            self._flush()

    def handle_data(self, data):
        if self.cur_segs is not None:
            self.buf += data.replace('\xa0', ' ').replace('　', ' ')


def parse_list_style(body):
    p = ListExamParser()
    p.feed(body)
    p._flush()
    qs = []
    for q in p.questions:
        segs = [s for s in q["segments"] if s["t"] == "img" or s["v"].strip()]
        if not segs:
            continue
        plain = " ".join(s["v"] for s in segs if s["t"] == "text")
        qs.append({"num": q["num"], "segments": segs,
                   "topics": classify(plain), "chars": len(plain)})
    return qs


def parse_file(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    # bodyを抽出
    mbody = re.search(r'<body[^>]*>(.*)</body>', raw, re.S | re.I)
    body = mbody.group(1) if mbody else raw
    # style/scriptを除去
    body = re.sub(r'<style[^>]*>.*?</style>', ' ', body, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', ' ', body, flags=re.S | re.I)
    body = re.sub(r'<!--.*?-->', ' ', body, flags=re.S)
    # mso条件コメントやNormal等のワード生成メタは後段のテキスト整形で概ね落ちる

    year_m = re.search(r'(20\d\d)\s*年度', raw)
    year = year_m.group(1) if year_m else os.path.basename(path)[:4]

    # 問題区切り: [問題 N] / 問題 N. / 問題N / 問題　１ など
    # マーカ位置を検出
    marker = re.compile(r'(?:\[\s*問題\s*([0-9０-９]+)\s*\]|問題\s*([0-9０-９]+)\s*[\.．]?)')
    # HTMLタグ越しに問題番号が改行される場合に備え、まず改行系を潰さずに探すが
    # タグの中に「問題\n1」があるケース（2016）に対応するため一旦タグ内改行を吸収
    body2 = re.sub(r'問題\s*\n\s*', '問題', body)

    matches = list(marker.finditer(body2))
    questions = []
    # 「問題 N」マーカが十分に無い場合はリスト形式として解析
    if len(matches) < 3:
        questions = parse_list_style(body)
        if questions:
            all_text = " ".join(s["v"] for q in questions for s in q["segments"] if s["t"] == "text")
            return {"year": year, "questions": questions, "topics": classify(all_text)}
    if not matches:
        segs = clean_block(body2)
        if segs:
            questions.append({"num": "全体", "segments": segs})
    else:
        for i, m in enumerate(matches):
            num = m.group(1) or m.group(2)
            # 全角数字を半角へ
            num = num.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body2)
            segs = clean_block(body2[start:end])
            plain = " ".join(s["v"] for s in segs if s["t"] == "text")
            questions.append({
                "num": num,
                "segments": segs,
                "topics": classify(plain),
                "chars": len(plain),
            })
    all_text = " ".join(s["v"] for q in questions for s in q["segments"] if s["t"] == "text")
    return {"year": year, "questions": questions, "topics": classify(all_text)}

def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*定期試験問題.html")) +
                   glob.glob(os.path.join(SRC_DIR, "* 定期試験問題.html")))
    files = sorted(set(files))
    exams = []
    for f in files:
        try:
            data = parse_file(f)
            exams.append(data)
            nq = len(data["questions"])
            print(f"{os.path.basename(f)}: {data['year']} -> {nq}問")
        except Exception as e:
            print("ERR", f, e)
    exams.sort(key=lambda x: x["year"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"exams": exams, "topics": list(TOPICS.keys())}, fh, ensure_ascii=False)
    size = os.path.getsize(OUT)
    print(f"\n書き出し: {OUT} ({size/1024:.0f} KB), {len(exams)}年度")

if __name__ == "__main__":
    main()
