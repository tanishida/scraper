# Mercari Scraper API

メルカリの検索結果上位5件の商品名と金額、画像と商品ページのURLを返却するAPI。

## 技術スタック

- **FastAPI** - APIサーバー
- **Playwright** - ブラウザ自動操作によるスクレイピング

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# Playwrightのブラウザをインストール
playwright install chromium
```

## 起動

```bash
# 実行権限を付与（初回のみ）
chmod +x start.sh

# サーバー起動
./start.sh
```

> ターミナルを開くたびに仮想環境の有効化が必要な場合：
> ```bash
> source .venv/bin/activate
> ```

## API仕様

### Swagger UI

```
http://localhost:8000/docs
```

| URL | 内容 |
|-----|------|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |
| `http://localhost:8000/openapi.json` | OpenAPI スキーマ |

### エンドポイント

#### `GET /search`

| パラメータ | 型 | 説明 |　必須 |
|-----------|-----|------|------|
| `keyword` | string | 検索キーワード | true |
| `query_params` | string | 検索条件 | false |

**リクエスト例**

```bash
curl "http://localhost:8000/search?keyword=Nintendo+Switch&query_params=status=sold_out&sort=created_time"
```

**レスポンス例**

```json
{
  "keyword": "Nintendo Switch",
  "results": [
    {"name": "Nintendo Switch 本体", "price": "25,000円","image_url": "https://static.mercdn.net/thumb/item/webp/mxxxxx.jpg?xxx", "item_url": "https://jp.mercari.com/item/mxxxx"},
    {"name": "Nintendo Switch Lite", "price": "15,000円","image_url": "https://static.mercdn.net/thumb/item/webp/mxxxxx.jpg?xxx", "item_url": "https://jp.mercari.com/item/mxxxx"}
  ]
}
```

## ファイル構成

```
scraper/
├── main.py          # APIサーバー
├── scraper.py       # スクレイピング処理
├── requirements.txt # 依存パッケージ
├── start.sh         # 起動スクリプト
└── README.md
```

## 注意事項

- メルカリのHTML構造が変更された場合、`scraper.py` のセレクタを更新する必要があります
