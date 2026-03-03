from playwright.async_api import async_playwright
from typing import Optional

async def scrape_mercari(keyword: str, query_params: Optional[str] = None) -> list[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ja-JP",
            timezone_id="Asia/Tokyo"
        )

        page = await context.new_page()

        # ==========================================
        # 爆速化1：画像、CSS、フォントの通信をすべて遮断！
        # ==========================================
        async def intercept_route(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                await route.abort() # 読み込まずに捨てる
            else:
                await route.continue_()

        await page.route("**/*", intercept_route)

        url = f"https://jp.mercari.com/search?keyword={keyword}"
        if query_params:
            url += f"&{query_params}"
            
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # 商品カードが読み込まれるまで待機
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)

        # ==========================================
        # 爆速化2：ブラウザ側（JS）で一括処理してPythonに返す！
        # ==========================================
        results = await page.evaluate('''() => {
            // ページ内のアイテムを10個取得
            const items = Array.from(document.querySelectorAll("li[data-testid='item-cell']")).slice(0, 10);
            
            // ループ処理をして、辞書のリストを作成して返す
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

        await browser.close()
        return results