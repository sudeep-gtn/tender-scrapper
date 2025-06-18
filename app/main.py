from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crawler.pipelines import Tender
import uvicorn
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import Query
import os
import subprocess
import json

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.get("/", response_class=HTMLResponse)
async def display_tenders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number for tenders"),
    per_page: int = Query(99, ge=1, le=100, description="Tenders per page"),
    url_page: int = Query(1, ge=1, description="Page number for indexed URLs"),
    url_per_page: int = Query(99, ge=1, le=100, description="URLs per page")
):
    try:
        # Read indexed_urls.json
        indexed_urls = []
        indexed_urls_file = "indexed_urls.json"
        if os.path.exists(indexed_urls_file):
            try:
                with open(indexed_urls_file, 'r', encoding='utf-8') as f:
                    indexed_urls = json.load(f)
                logger.info(f"Loaded {len(indexed_urls)} URLs from {indexed_urls_file}")
                logger.debug(f"Indexed URLs sample: {indexed_urls[:2]}")
            except Exception as e:
                logger.error(f"Error reading {indexed_urls_file}: {e}")
        else:
            logger.error(f"{indexed_urls_file} not found in root directory")

        # Paginate indexed URLs
        url_offset = (url_page - 1) * url_per_page
        paginated_urls = indexed_urls[url_offset:url_offset + url_per_page]
        total_urls = len(indexed_urls)
        total_url_pages = (total_urls + url_per_page - 1) // url_per_page

        # Connect to database
        engine = create_engine('sqlite:///tenders.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Calculate offset for tenders
        offset = (page - 1) * per_page
        
        # Query all tenders with pagination
        tenders_query = session.query(Tender).order_by(Tender.pub_date.desc())
        
        # Get total count for tenders pagination
        total_tenders = tenders_query.count()
        total_pages = (total_tenders + per_page - 1) // per_page
        
        # Fetch paginated tenders
        tenders = tenders_query.offset(offset).limit(per_page).all()
        
        logger.info(f"Loaded {len(tenders)} tenders (page {page}, {per_page} per page, total {total_tenders})")
        logger.debug(f"Tenders sample: {[{'title': t.title, 'issuer': t.issuer} for t in tenders[:2]]}")
        
        session.close()
        
        # Nepal timezone (+0545)
        nepal_time = datetime.now(ZoneInfo("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "tenders": tenders,
                "indexed_urls": paginated_urls,
                "current_time": nepal_time,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_tenders": total_tenders,
                "url_page": url_page,
                "url_per_page": url_per_page,
                "total_url_pages": total_url_pages,
                "total_urls": total_urls
            }
        )
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        nepal_time = datetime.now(ZoneInfo("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S %Z")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "tenders": [],
                "indexed_urls": [],
                "current_time": nepal_time,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "total_tenders": 0,
                "url_page": url_page,
                "url_per_page": url_per_page,
                "total_url_pages": 0,
                "total_urls": 0
            }
        )

def run_crawler():
    try:
        result = subprocess.run(["python", "run_crawler.py"], check=True, text=True, capture_output=True)
        logger.info(f"Crawler executed: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running crawler: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error running crawler: {e}")

if __name__ == "__main__":
    run_crawler()
    logger.info("Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)