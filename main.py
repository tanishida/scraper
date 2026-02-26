from fastapi import FastAPI, Query, HTTPException
from typing import Optional
from scraper import scrape_mercari

app = FastAPI()

@app.get("/search")
async def search(
    keyword: str = Query(..., description="検索キーワード"),
    query_params: Optional[str] = Query(None, description="メルカリURLに追加するクエリパラメータ (例: status=sold_out&sort=created_time)")
):
    try:
        results = await scrape_mercari(keyword, query_params)
        return {"keyword": keyword, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
