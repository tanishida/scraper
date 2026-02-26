from playwright.async_api import async_playwright
from typing import Optional

async def scrape_mercari(keyword: str, query_params: Optional[str] = None) -> list[dict]:
    async with async_playwright() as p:
        ## localhostでの開発用
        # browser = await p.chromium.launch(headless=False)
        
        ## EC2などのサーバー用
        browser = await p.chromium.launch(headless=True)        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}, # 画面サイズをフルHDに偽装
            locale="ja-JP", # 日本からのアクセスであることを強調
            timezone_id="Asia/Tokyo" # タイムゾーンも日本に合わせる
        )

        ## ラズパイよう
        # browser = await p.chromium.launch(executable_path='/usr/bin/chromium-browser',headless=True)
        # context = await browser.new_context(
        #  user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        #)
        page = await context.new_page()

        url = f"https://jp.mercari.com/search?keyword={keyword}"
        if query_params:
            url += f"&{query_params}"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        ## 商品カードが読み込まれるまで待機
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)
        items = await page.query_selector_all("li[data-testid='item-cell']")
        
        items = await page.locator("li[data-testid='item-cell']").all()

        results = []
        for item in items[:10]:
            name_el = await item.query_selector("span[data-testid='thumbnail-item-name']")
            price_el = await item.query_selector("span[class*='number']")
            img_el = await item.query_selector("img")
            link_el = await item.query_selector("a")

            name = await name_el.inner_text() if name_el else "不明"
            price = await price_el.inner_text() + "円" if price_el else "不明"
            img_url = await img_el.get_attribute("src") if img_el else "不明"
            item_path = await link_el.get_attribute("href") if link_el else None
            item_url = f"https://jp.mercari.com{item_path}" if item_path else "不明"

            results.append({
                "name": name,
                "price": price,
                "image_url": img_url,
                "item_url": item_url,
            })

        await browser.close()
        return results
