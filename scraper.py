# scraper.py
from playwright.async_api import Browser
from typing import Optional
import urllib.parse
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# ★ ポイント：引数に「browser: Browser」を受け取るようにする！
async def fetch_mercari_items(browser: Browser, keyword: str, query_params: Optional[str] = None) -> list[dict]:
    
# 受け取ったブラウザから、新しいタブ（コンテキスト）を作る
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="ja-JP",
        timezone_id="Asia/Tokyo",
        
        geolocation={"latitude": 35.6895, "longitude": 139.6917}, # 東京の座標
        permissions=["geolocation"],
        extra_http_headers={
            "Accept-Language": "ja-JP,ja;q=0.9",
            # 日本の一般的なプロバイダ（OCNなど）のIPアドレスを「本当の送信元」として申告する
            "X-Forwarded-For": "114.164.255.255", 
            "X-Real-IP": "114.164.255.255"
        }
    )
    
    page = await context.new_page()
    await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {},
            };
        """)

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
        # （URLを開いたあとの処理）
        await page.goto(url, wait_until="load", timeout=60000)

        # ★ 修正箇所：商品が出てくるのを待つ処理を、安全なtry-exceptで囲む
        try:
            await page.wait_for_selector("li[data-testid='item-cell']", timeout=30000)
        except PlaywrightTimeoutError:
            # 30秒待っても商品が出なかった場合の緊急処理
            print("🚨 タイムアウト発生！商品が見つかりません。現在の画面を撮影します。")
            
            # 原因究明のために、Playwrightが見ている画面を画像として保存！
            await page.screenshot(path="error_screen.png", full_page=True)
            
            # APIをクラッシュさせず、安全に「空のリスト」をiOSに返す
            return []
        # 3. JS側で一括処理してPythonに返す
        results = await page.evaluate('''() => {
            const allItems = Array.from(document.querySelectorAll("li[data-testid='item-cell']"));
            const validItems = [];

            for (const item of allItems) {
                // 🚨 罠1の対策：「PR」という文字が含まれている広告アイテムは絶対に無視！
                if (item.innerText.includes("PR")) {
                    continue;
                }

                // 🚨 最大の罠（ボット対策）の対策：
                // メルカリが勝手に「販売中」を混ぜてくるなら、自力で「売り切れ」だけを判別する！
                // 売り切れ商品には必ず「売り切れ」というテキストや、SOLDバッジのデータが含まれます。
                const itemHTML = item.innerHTML;
                const isSoldOut = itemHTML.includes('売り切れ') || 
                                  itemHTML.includes('sticker="sold"') || 
                                  itemHTML.includes('SOLD');
                
                // もし「売り切れ」じゃなかったら（＝販売中なら）、スキップして次を探す！
                if (!isSoldOut) {
                    continue;
                }

                const nameEl = item.querySelector("span[data-testid='thumbnail-item-name']");
                
                // ★ 究極の金額取得ロジック（海外通貨・小数点ブロック機能付き）
                let cleanPrice = "価格不明";
                const merPriceTag = item.querySelector('mer-price');
                const merPriceClass = item.querySelector('.merPrice');
                
                // 1. まず、絶対に為替の影響を受けない「裏データ（value属性）」を狙う！
                if (merPriceTag && merPriceTag.getAttribute('value')) {
                    const rawValue = merPriceTag.getAttribute('value');
                    cleanPrice = rawValue + "円";
                } else {
                    // 2. もし画面のテキストから取る場合は、海外通貨の「小数点」がないかチェック！
                    let textPrice = "";
                    if (merPriceClass) {
                        textPrice = merPriceClass.innerText;
                    } else {
                        const match = item.innerText.match(/[0-9,\.]+/);
                        if (match) textPrice = match[0];
                    }

                    // 「.（小数点）」が含まれていたら、それは外貨なので採用しない！
                    if (textPrice.includes(".")) {
                        cleanPrice = "海外通貨エラー";
                    } else {
                        cleanPrice = textPrice.replace(/[^0-9]/g, "") + "円";
                    }
                }

                const linkEl = item.querySelector('a');
                const imgEl = item.querySelector('img');

                validItems.push({
                    name: nameEl ? nameEl.innerText : "",
                    price: cleanPrice,
                    item_url: linkEl ? "https://jp.mercari.com" + linkEl.getAttribute('href') : "",
                    image_url: imgEl ? imgEl.getAttribute('src') : ""
                });

                // 「本物の売り切れデータ」が10件集まったら終了
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