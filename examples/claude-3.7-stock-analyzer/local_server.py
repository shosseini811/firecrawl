from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI()

# Models to match Firecrawl's API structure
class MapResponse(BaseModel):
    links: List[str]
    content: Optional[str] = None

class ScrapeResponse(BaseModel):
    success: bool = True
    data: List[Dict[str, Any]] = []
    error: Optional[str] = None

def get_stock_page(symbol: str) -> Optional[str]:
    """Get stock page content from Robinhood"""
    try:
        url = f"https://robinhood.com/stocks/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"Error fetching stock page: {e}")
        return None

class MapRequest(BaseModel):
    url: str
    search: Optional[str] = None

@app.post("/v1/map")
async def map_url(request: MapRequest):
    """Map endpoint to find relevant stock pages"""
    try:
        # For stocks, we'll construct the URL directly
        if request.search:
            # Convert search term to uppercase as stock symbols are uppercase
            symbol = request.search.upper()
            return {
                "success": True,
                "data": {
                    "links": [f"https://robinhood.com/stocks/{symbol}"],
                    "content": f"Found stock page for {symbol}"
                }
            }
        return {
            "success": True,
            "data": {
                "links": [],
                "content": "No search term provided"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class ScrapeRequest(BaseModel):
    url: str
    formats: Optional[List[str]] = None

@app.post("/v1/scrape")
async def scrape_url(request: ScrapeRequest):
    """Scrape endpoint to get stock information"""
    try:
        # Extract stock symbol from URL
        symbol = request.url.split("/")[-1]
        content = get_stock_page(symbol)
        
        if content:
            # Parse the HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text()
            
            # Create response in Firecrawl format
            return {
                "success": True,
                "data": [{
                    "url": request.url,
                    "markdown": text_content,
                    "html": content
                }]
            }
        else:
            return {
                "success": False,
                "error": f"Failed to fetch content for {symbol}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/v1/search")
async def search(query: str):
    """Search endpoint (simplified version)"""
    try:
        symbol = query.upper()
        return {
            "success": True,
            "data": [{
                "url": f"https://robinhood.com/stocks/{symbol}",
                "title": f"Stock: {symbol}",
                "snippet": f"Information about {symbol} stock"
            }]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting local Firecrawl server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
