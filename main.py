from fastapi import FastAPI, Query, HTTPException
from scraper import scrape_mercari

app = FastAPI()

@app.get("/search")
async def search(keyword: str = Query(..., description="検索キーワード")):
    try:
        results = await scrape_mercari(keyword)
        return {"keyword": keyword, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
