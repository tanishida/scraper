# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from playwright.async_api import async_playwright, Browser, Playwright
from typing import Optional

# ★ 追加：別ファイルに分けた関数をインポートする
from scraper import fetch_mercari_items

playwright_instance: Optional[Playwright] = None
browser_instance: Optional[Browser] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright_instance, browser_instance
    print("🚀 サーバー起動：Playwrightのブラウザを立ち上げます...")
    playwright_instance = await async_playwright().start()
    browser_instance = await playwright_instance.chromium.launch(headless=True)
    print("✅ ブラウザの待機完了！APIの受付を開始します。")
    
    yield
    
    print("🛑 サーバー停止：ブラウザを終了します...")
    if browser_instance:
        await browser_instance.close()
    if playwright_instance:
        await playwright_instance.stop()

app = FastAPI(lifespan=lifespan)

# ==========================================
# APIエンドポイント
# ==========================================
@app.get("/api/scrape")
async def scrape_mercari_api(keyword: str, query_params: Optional[str] = None):
    global browser_instance
    
    if not browser_instance:
        return {"error": "ブラウザが起動していません"}

    # ★ 変更：別ファイルの関数に、起動済みのブラウザ（browser_instance）を渡して実行するだけ！
    results = await fetch_mercari_items(browser=browser_instance, keyword=keyword, query_params=query_params)
    
    return results