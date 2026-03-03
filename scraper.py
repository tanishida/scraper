# scraper.py
from playwright.async_api import Browser
from typing import Optional

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

        # 2. ターゲットURLの構築
        url = f"https://jp.mercari.com/search?keyword={keyword}"
        if query_params:
            url += f"&{query_params}"
            
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)

        # 3. JS側で一括処理してPythonに返す
        results = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll("li[data-testid='item-cell']")).slice(0, 10);
            return items.map(item => {
                const nameEl = item.querySelector("span[data-testid='thumbnail-item-name']");
                const priceEl = item.querySelector("span[class*='number']");
                const linkEl = item.querySelector('a');
                const imgEl = item.querySelector('img');

                return {
                    name: nameEl ? nameEl.innerText : "",
                    price: priceEl ? priceEl.innerText + "円" : "",
                    item_url: linkEl ? "https://jp.mercari.com" + linkEl.getAttribute('href') : "",
                    image_url: imgEl ? imgEl.getAttribute('src') : ""
                };
            });
        }''')
        
        return results

    finally:
        # 必ず最後にコンテキスト（タブ）を閉じる！
        await context.close()