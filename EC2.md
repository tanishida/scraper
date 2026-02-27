## API更新手順

```bash
# EC2 ssh接続
ssh -i scraping.pem ubuntu@（ElasticIP）

# （準備）作業フォルダにいることを確認
cd ~/scraper

# 1. 最新のコードをダウンロードする
git pull

# 2. 【超重要】裏で動いているAPIを再起動して、新しいコードを読み込ませる
sudo systemctl restart scraper
```