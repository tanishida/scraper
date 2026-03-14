# scraper.py
from playwright.async_api import Browser
from typing import Optional
import urllib.parse

# ★ ポイント：引数に「browser: Browser」を受け取るようにする！
async def fetch_mercari_items(browser: Browser, keyword: str, query_params: Optional[str] = None) -> list[dict]:
    
    # 受け取ったブラウザから、新しいタブ（コンテキスト）を作る
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="ja-JP",
        timezone_id="Asia/Tokyo"
    )
    
    page = await context.new_page()

    try:
        # 1. 画像・CSSなどの無駄な通信を遮断
        async def intercept_route(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*", intercept_route)

        # 2. ターゲットURLの構築（最強のエンコード版）
        base_url = "https://jp.mercari.com/search"
        params = {"keyword": keyword}

        if query_params:
            # iOSからの文字列を一度完全に解凍（%257C -> | など）
            clean_query = urllib.parse.unquote(urllib.parse.unquote(query_params))
            
            # "key=value&key2=value2" の文字列を分解して辞書に追加
            for k, v in urllib.parse.parse_qsl(clean_query):
                params[k] = v

        # 辞書を完璧なURLエンコード文字列に再構築
        # （quote_viaを指定することで、スペースを確実な "%20" に、| を "%7C" に変換します）
        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{base_url}?{encoded_params}"
            
        print(f"🌍 Playwrightが開く完璧なURL: {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)

        # 3. JS側で一括処理してPythonに返す
        results = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll("li[data-testid='item-cell']")).slice(0, 10);
            return items.map(item => {
                const nameEl = item.querySelector("span[data-testid='thumbnail-item-name']");
                
                // ★ あなたの神デバッグを反映した完璧なセレクタ！
                // 「merPriceクラス」の中にある「class名にnumberを含むspan」をピンポイントで狙撃
                const priceEl = item.querySelector('.merPrice span[class*="number"]');
                
                let priceStr = "";
                if (priceEl) {
                    priceStr = priceEl.innerText;
                }
                
                // 数字以外の文字（カンマなど）を綺麗に消して「円」をつける
                const cleanPrice = priceStr ? priceStr.replace(/[^0-9]/g, "") + "円" : "価格不明";

                const linkEl = item.querySelector('a');
                const imgEl = item.querySelector('img');

                return {
                    name: nameEl ? nameEl.innerText : "",
                    price: cleanPrice,
                    item_url: linkEl ? "https://jp.mercari.com" + linkEl.getAttribute('href') : "",
                    image_url: imgEl ? imgEl.getAttribute('src') : ""
                };
            });
        }''')
        
        return results

    finally:
        # 必ず最後にコンテキスト（タブ）を閉じる！
        await context.close()