import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.document_service import ingest_document
from services.scraper_service import scrape_web 
from services.login_service import automate_login_test
from services.notion_service import NotionService
from services.email_service import EmailService
from core.validators import validate_url

router = APIRouter(prefix="/documents", tags=["Documents"])

class ScrapeRequest(BaseModel):
    url: str

class NotionRequest(BaseModel):
    title: str
    content: str

class EmailRequest(BaseModel):
    email: str
    subject: str
    body: str

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads and ingests a .txt file into the RAG memory."""
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    content = await file.read()
    text = content.decode("utf-8")
    
    count = ingest_document(title=file.filename, content=text)
    return {"filename": file.filename, "chunks_ingested": count}

@router.post("/scrape")
async def scrape_resource(data: ScrapeRequest):
    """Triggers the stealth Playwright scraper for a specific URL."""
    is_valid, error_msg = validate_url(data.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error_msg}")
    
    try:
        result_msg = await scrape_web(data.url, conversation_id=0)
        return {"url": data.url, "detail": result_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notion")
async def send_to_notion(data: NotionRequest):
    """Exports content to a structured Notion page."""
    notion = NotionService()
    success = notion.create_page(title=data.title, content=data.content)
    if success:
        return {"status": "success", "message": "Notion page created"}
    raise HTTPException(status_code=500, detail="Failed to create Notion page")

@router.post("/email")
async def send_email_report(data: EmailRequest):
    """Dispatches a professional report via Resend."""
    try:
        email_svc = EmailService()
        success = email_svc.send_email(
            to_email=data.email, 
            subject=data.subject, 
            content=data.body
        )
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Email service failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-login")
async def run_login_test():
    """Automated login verification test."""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, automate_login_test)
        return {"status": "ok", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))