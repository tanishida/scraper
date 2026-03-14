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
        # async def intercept_route(route):
          #  if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
           #     await route.abort()
            #else:
             #   await route.continue_()
 #       await page.route("**/*", intercept_route)

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
        
# domcontentloaded（骨組みだけ）ではなく、load（全体読み込み完了）まで待ちます
        await page.goto(url, wait_until="load", timeout=60000)
        
       # ★ 新規追加：URLで絞り込みが無視された時のために、Playwrightに「物理的に」売り切れボタンを押させる！
        try:
            # サイドバーの「売り切れ」チェックボックス（label要素）を探してクリック
            await page.locator('label').filter(has_text="売り切れ").click(timeout=3000)
            print("👆 画面上の「売り切れ」チェックボックスを物理的にクリックしました！")
            # 画面が切り替わるのを待つ
            await page.wait_for_timeout(3000)
        except Exception:
            print("ℹ️ チェックボックスが見つからない、または既に売り切れ状態です。そのまま進みます。")

        # 商品が読み込まれるのを待つ
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)

        # 3. JS側で一括処理してPythonに返す
        results = await page.evaluate('''() => {
            const allItems = Array.from(document.querySelectorAll("li[data-testid='item-cell']"));
            const validItems = [];

            for (const item of allItems) {
                // ★ 罠1の対策：「PR」という文字が含まれている広告アイテムは絶対に無視する！
                if (item.innerText.includes("PR")) {
                    continue;
                }

                const nameEl = item.querySelector("span[data-testid='thumbnail-item-name']");
                
                // 金額の取得（神デバッグで見つけた完璧なセレクタ）
                const priceEl = item.querySelector('.merPrice span[class*="number"]');
                let priceStr = priceEl ? priceEl.innerText : "";
                const cleanPrice = priceStr ? priceStr.replace(/[^0-9]/g, "") + "円" : "価格不明";

                const linkEl = item.querySelector('a');
                const imgEl = item.querySelector('img');

                validItems.push({
                    name: nameEl ? nameEl.innerText : "",
                    price: cleanPrice,
                    item_url: linkEl ? "https://jp.mercari.com" + linkEl.getAttribute('href') : "",
                    image_url: imgEl ? imgEl.getAttribute('src') : ""
                });

                // 綺麗なデータが10件集まったらループを終了
                if (validItems.length >= 10) {
                    break;
                }
            }
            return validItems;
        }''')
        
        return results

    finally:
        # 必ず最後にコンテキスト（タブ）を閉じる！
        await context.close()