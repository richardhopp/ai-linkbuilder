import os
import json
import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from dotenv import load_dotenv
import time
import threading

# Import your link builder class - adjust path as needed
from high_quality_link_builder import HighQualityLinkBuilder

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="High-Quality Link Builder API",
    description="API for running high-quality backlink campaigns on premium sites",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up basic authentication
API_KEY = os.getenv("API_KEY", "your-default-api-key")

# Store campaign results
campaign_results = {}
campaign_status = {}
active_campaigns = {}

# API key validation dependency
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Models
class SiteConfig(BaseModel):
    url: str
    description: str
    keywords: List[str]

class CampaignConfig(BaseModel):
    ahrefs_api_key: str
    openai_api_key: Optional[str] = None
    twocaptcha_api_key: Optional[str] = None
    min_domain_rating: int = 50
    min_organic_traffic: int = 500
    max_external_links: int = 100
    exclude_subdomains: bool = True
    max_threads: int = 3
    sites_per_type: int = 3
    target_site_types: List[str] = ["forums", "blogs", "qa_sites", "directories", "social_bookmarks"]
    sites_data: Dict[str, SiteConfig] = {}

# Run campaign in the background
def run_campaign_task(campaign_id: str, config: CampaignConfig):
    try:
        campaign_status[campaign_id] = "running"
        
        # Create link builder instance
        link_builder = HighQualityLinkBuilder()
        active_campaigns[campaign_id] = link_builder
        
        # Configure the link builder
        link_builder.config["ahrefs_api_key"] = config.ahrefs_api_key
        if config.openai_api_key:
            link_builder.config["openai_api_key"] = config.openai_api_key
        if config.twocaptcha_api_key:
            link_builder.config["twocaptcha_api_key"] = config.twocaptcha_api_key
            
        link_builder.config["min_domain_rating"] = config.min_domain_rating
        link_builder.config["min_organic_traffic"] = config.min_organic_traffic
        link_builder.config["max_external_links"] = config.max_external_links
        link_builder.config["exclude_subdomains"] = config.exclude_subdomains
        link_builder.config["max_threads"] = config.max_threads
        link_builder.config["target_site_types"] = config.target_site_types
        
        # Set up sites data if provided
        if config.sites_data:
            link_builder.sites_data = {
                name: {
                    "url": site.url,
                    "description": site.description,
                    "keywords": site.keywords
                }
                for name, site in config.sites_data.items()
            }
        
        # Run the campaign
        results = link_builder.run_campaign(sites_per_type=config.sites_per_type)
        
        # Store results
        campaign_results[campaign_id] = results
        campaign_status[campaign_id] = "completed"
        
        # Cleanup
        link_builder.cleanup()
        del active_campaigns[campaign_id]
        
    except Exception as e:
        logging.error(f"Campaign error: {str(e)}")
        campaign_status[campaign_id] = f"failed: {str(e)}"
        
        # Cleanup if link builder was created
        if campaign_id in active_campaigns:
            try:
                active_campaigns[campaign_id].cleanup()
                del active_campaigns[campaign_id]
            except:
                pass

# API Endpoints
@app.post("/campaigns/", status_code=202, dependencies=[Depends(verify_api_key)])
async def start_campaign(config: CampaignConfig, background_tasks: BackgroundTasks):
    """Start a new link building campaign."""
    campaign_id = f"campaign_{int(time.time())}"
    
    # Start campaign in background
    background_tasks.add_task(run_campaign_task, campaign_id, config)
    
    return {"campaign_id": campaign_id, "status": "started"}

@app.get("/campaigns/{campaign_id}/status", dependencies=[Depends(verify_api_key)])
async def get_campaign_status(campaign_id: str):
    """Get the status of a campaign."""
    if campaign_id not in campaign_status:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    return {"campaign_id": campaign_id, "status": campaign_status[campaign_id]}

@app.get("/campaigns/{campaign_id}/results", dependencies=[Depends(verify_api_key)])
async def get_campaign_results(campaign_id: str):
    """Get the results of a completed campaign."""
    if campaign_id not in campaign_status:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if campaign_status[campaign_id] != "completed":
        return {"campaign_id": campaign_id, "status": campaign_status[campaign_id], "results": None}
        
    return {
        "campaign_id": campaign_id, 
        "status": campaign_status[campaign_id],
        "results": campaign_results.get(campaign_id)
    }

@app.delete("/campaigns/{campaign_id}", dependencies=[Depends(verify_api_key)])
async def cancel_campaign(campaign_id: str):
    """Cancel a running campaign."""
    if campaign_id not in campaign_status:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if campaign_id in active_campaigns:
        try:
            active_campaigns[campaign_id].cleanup()
            del active_campaigns[campaign_id]
            campaign_status[campaign_id] = "cancelled"
            return {"campaign_id": campaign_id, "status": "cancelled"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cancelling campaign: {str(e)}")
    else:
        return {"campaign_id": campaign_id, "status": campaign_status[campaign_id]}

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "High-Quality Link Builder API. See /docs for documentation."}

# Run the app if this file is executed directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
