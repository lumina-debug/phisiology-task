# 生理学A 定期試験 対策アプリ

早稲田大学「生理学A（旧 生理学I）」定期試験の**過去問17年分（2008〜2025年度・全250問）**を教材化した、ブラウザだけで動く学習用Webアプリです。講義ノート（`26 生理学A 講義ノート *.pdf`）と過去問（`*定期試験問題.html`）をもとに作成しました。

## 使い方

`docs/index.html` をブラウザで開くだけです（サーバー不要・オフライン動作）。

```
open docs/index.html          # macOS
xdg-open docs/index.html      # Linux
# または index.html をダブルクリック
```

進捗・解答メモはブラウザの localStorage に保存されるため、次回開いたときも残ります。

### スマホでも見たい場合（GitHub Pages で公開リンクを作る）

1. GitHub のこのリポジトリ → **Settings** → 左メニュー **Pages**
2. **Build and deployment** の **Source** で「**Deploy from a branch**」を選択
3. **Branch** を `claude/physiology-exam-prep-app-0cvtmq`、フォルダを **`/docs`** にして **Save**
4. 1〜2分待つと公開URL `https://lumina-debug.github.io/phisiology-task/` が発行され、PC・スマホどちらでも開けます

`/docs` フォルダだけが公開されるため、講義ノートPDFや過去問の元HTMLはネット上には公開されません。

## 機能

| 画面 | 内容 |
|------|------|
| 📊 **ダッシュボード** | 全設問をテーマ分類した**頻出テーマランキング**と学習進捗サマリ。頻出分野が一目でわかります。 |
| 📅 **年度別** | 各年度の全設問を表示。問題文・図表（画像）・小問を確認でき、解答メモと「理解した／復習中」の進捗を記録。 |
| 🏷 **テーマ別** | 同一テーマの問題を全年度から横断表示。頻出分野の「問われ方」の変遷を追えます。 |
| 🃏 **一問一答** | 頻出テーマに対応した55枚のフラッシュカード。用語・定義の暗記に。キーボード操作対応。 |
| 📝 **模擬試験** | 頻出テーマからランダム出題。本番形式で自力演習。 |
| 🔍 **検索** | 全250問をキーワード検索（例：ADH、活動電位、GFR、インスリン）。 |

## データ生成（開発者向け）

過去問HTMLからデータを再生成する場合：

```bash
python3 scripts/extract_exams.py   # *定期試験問題.html -> docs/exams.json
python3 scripts/build_data.py      # exams.json + flashcards.json -> docs/data.js
```

- `scripts/extract_exams.py` — 過去問HTMLを問題単位に構造化し、図表（データURI画像）を保持したままJSON化。キーワードによるテーマ自動分類も行う。
- `docs/flashcards.json` — 一問一答の参考解答（手作業で作成）。
- `docs/data.js` — `index.html` が `file://` でも読めるよう、上記JSONをJSにまとめたもの。

## 注意

一問一答の解答は標準的な生理学に基づく**学習用の参考解答**です。実際の採点基準は講義ノートの記述に従ってください。
