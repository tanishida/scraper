from playwright.async_api import async_playwright

async def scrape_mercari(keyword: str) -> list[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        url = f"https://jp.mercari.com/search?keyword={keyword}&status=sold_out&category_id=1296&item_condition_id=1%2C2&shipping_payer_id=2&sort=created_time&order=desc"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # 商品カードが読み込まれるまで待機
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)

        items = await page.query_selector_all("li[data-testid='item-cell']")

        results = []
        for item in items[:5]:
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
