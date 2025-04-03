import os
import json
import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Header, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
from dotenv import load_dotenv
import time
import threading

# Import link builder class
from high_quality_link_builder import HighQualityLinkBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="High-Quality Link Builder API",
    description="API for running high-quality backlink campaigns on premium sites",
    version="1.0.0"
)

# Set up templates for the UI
templates = Jinja2Templates(directory="templates")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Create the main index.html template
with open("templates/index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>High-Quality Link Builder</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f5f5f5;
        }
        .container {
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #2c3e50;
            color: #fff;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0;
            padding: 0 20px;
        }
        .card {
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        select[multiple] {
            height: 120px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #2980b9;
        }
        .result-container {
            margin-top: 30px;
            display: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 2s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            color: #e74c3c;
            padding: 10px;
            background-color: #fadbd8;
            border-radius: 4px;
            margin-bottom: 15px;
            display: none;
        }
        .nav-tabs {
            display: flex;
            list-style-type: none;
            padding: 0;
            margin: 0 0 20px 0;
            border-bottom: 1px solid #ddd;
        }
        .nav-tabs li {
            margin-right: 5px;
        }
        .nav-tabs li a {
            display: block;
            padding: 10px 15px;
            text-decoration: none;
            color: #333;
            border: 1px solid transparent;
            border-radius: 4px 4px 0 0;
        }
        .nav-tabs li a.active {
            border: 1px solid #ddd;
            border-bottom-color: #fff;
            background-color: #fff;
            margin-bottom: -1px;
        }
        #campaignStatus, #campaignResults {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>High-Quality Link Builder</h1>
        </div>
    </header>
    
    <div class="container">
        <ul class="nav-tabs">
            <li><a href="#newCampaign" class="active" id="newCampaignTab">New Campaign</a></li>
            <li><a href="#checkStatus" id="checkStatusTab">Check Status</a></li>
            <li><a href="#viewResults" id="viewResultsTab">View Results</a></li>
            <li><a href="/docs" target="_blank">API Docs</a></li>
        </ul>
        
        <div id="newCampaign" class="tab-content active-tab">
            <div class="card">
                <h2>Start a New Link Building Campaign</h2>
                <div class="error" id="newCampaignError"></div>
                
                <form id="campaignForm">
                    <div class="form-group">
                        <label for="ahrefs_api_key">Ahrefs API Key</label>
                        <input type="text" id="ahrefs_api_key" name="ahrefs_api_key" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="openai_api_key">OpenAI API Key (Optional)</label>
                        <input type="text" id="openai_api_key" name="openai_api_key">
                    </div>
                    
                    <div class="form-group">
                        <label for="twocaptcha_api_key">2Captcha API Key (Optional)</label>
                        <input type="text" id="twocaptcha_api_key" name="twocaptcha_api_key">
                    </div>
                    
                    <div class="form-group">
                        <label for="min_domain_rating">Minimum Domain Rating (0-100)</label>
                        <input type="number" id="min_domain_rating" name="min_domain_rating" min="0" max="100" value="50">
                    </div>
                    
                    <div class="form-group">
                        <label for="min_organic_traffic">Minimum Organic Traffic</label>
                        <input type="number" id="min_organic_traffic" name="min_organic_traffic" min="0" value="500">
                    </div>
                    
                    <div class="form-group">
                        <label for="max_external_links">Maximum External Links</label>
                        <input type="number" id="max_external_links" name="max_external_links" min="0" value="100">
                    </div>
                    
                    <div class="form-group">
                        <label for="exclude_subdomains">Exclude Subdomains</label>
                        <select id="exclude_subdomains" name="exclude_subdomains">
                            <option value="true" selected>Yes</option>
                            <option value="false">No</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="max_threads">Maximum Concurrent Threads (1-10)</label>
                        <input type="number" id="max_threads" name="max_threads" min="1" max="10" value="3">
                    </div>
                    
                    <div class="form-group">
                        <label for="sites_per_type">Number of Sites per Type (1-20)</label>
                        <input type="number" id="sites_per_type" name="sites_per_type" min="1" max="20" value="3">
                    </div>
                    
                    <div class="form-group">
                        <label for="target_site_types">Target Site Types</label>
                        <select id="target_site_types" name="target_site_types" multiple required>
                            <option value="forums" selected>Forums</option>
                            <option value="blogs" selected>Blogs</option>
                            <option value="qa_sites" selected>Q&A Sites</option>
                            <option value="directories">Directories</option>
                            <option value="social_bookmarks">Social Bookmarks</option>
                            <option value="wiki_sites">Wiki Sites</option>
                            <option value="comment_sections">Comment Sections</option>
                        </select>
                        <small>Hold Ctrl (or Cmd on Mac) to select multiple options</small>
                    </div>
                    
                    <button type="submit">Start Campaign</button>
                </form>
                
                <div class="loading" id="newCampaignLoading">
                    <div class="spinner"></div>
                    <p>Starting campaign, please wait...</p>
                </div>
                
                <div class="result-container" id="newCampaignResult">
                    <h3>Campaign Started</h3>
                    <p>Your campaign has been started successfully. Use the campaign ID below to check status.</p>
                    <p><strong>Campaign ID:</strong> <span id="campaignId"></span></p>
                </div>
            </div>
        </div>
        
        <div id="checkStatus" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Check Campaign Status</h2>
                <div class="error" id="statusError"></div>
                
                <form id="statusForm">
                    <div class="form-group">
                        <label for="status_campaign_id">Campaign ID</label>
                        <input type="text" id="status_campaign_id" name="campaign_id" required>
                    </div>
                    
                    <button type="submit">Check Status</button>
                </form>
                
                <div class="loading" id="statusLoading">
                    <div class="spinner"></div>
                    <p>Fetching status, please wait...</p>
                </div>
                
                <div class="result-container" id="campaignStatus">
                    <h3>Campaign Status</h3>
                    <p><strong>Status:</strong> <span id="status"></span></p>
                </div>
            </div>
        </div>
        
        <div id="viewResults" class="tab-content" style="display:none;">
            <div class="card">
                <h2>View Campaign Results</h2>
                <div class="error" id="resultsError"></div>
                
                <form id="resultsForm">
                    <div class="form-group">
                        <label for="results_campaign_id">Campaign ID</label>
                        <input type="text" id="results_campaign_id" name="campaign_id" required>
                    </div>
                    
                    <button type="submit">View Results</button>
                </form>
                
                <div class="loading" id="resultsLoading">
                    <div class="spinner"></div>
                    <p>Fetching results, please wait...</p>
                </div>
                
                <div class="result-container" id="campaignResults">
                    <h3>Campaign Results</h3>
                    <div id="resultsContent"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // API Key from UI
            let apiKey = '';
            
            // Check if API key is stored in localStorage
            if (localStorage.getItem('apiKey')) {
                apiKey = localStorage.getItem('apiKey');
            } else {
                // If no API key, prompt for one
                apiKey = prompt('Please enter your API key:');
                if (apiKey) {
                    localStorage.setItem('apiKey', apiKey);
                } else {
                    showError('newCampaignError', 'API key is required to use this application.');
                }
            }
            
            // Tab navigation
            document.getElementById('newCampaignTab').addEventListener('click', function(e) {
                e.preventDefault();
                showTab('newCampaign');
            });
            
            document.getElementById('checkStatusTab').addEventListener('click', function(e) {
                e.preventDefault();
                showTab('checkStatus');
            });
            
            document.getElementById('viewResultsTab').addEventListener('click', function(e) {
                e.preventDefault();
                showTab('viewResults');
            });
            
            // Form submissions
            document.getElementById('campaignForm').addEventListener('submit', function(e) {
                e.preventDefault();
                startCampaign();
            });
            
            document.getElementById('statusForm').addEventListener('submit', function(e) {
                e.preventDefault();
                checkStatus();
            });
            
            document.getElementById('resultsForm').addEventListener('submit', function(e) {
                e.preventDefault();
                viewResults();
            });
            
            // Function to show a specific tab
            function showTab(tabId) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(function(tab) {
                    tab.style.display = 'none';
                });
                
                // Show the selected tab
                document.getElementById(tabId).style.display = 'block';
                
                // Update active tab in navigation
                document.querySelectorAll('.nav-tabs a').forEach(function(tab) {
                    tab.classList.remove('active');
                });
                document.getElementById(tabId + 'Tab').classList.add('active');
            }
            
            // Start a new campaign
            function startCampaign() {
                // Hide previous results and errors
                document.getElementById('newCampaignResult').style.display = 'none';
                document.getElementById('newCampaignError').style.display = 'none';
                
                // Show loading spinner
                document.getElementById('newCampaignLoading').style.display = 'block';
                
                // Gather form data
                const data = {
                    ahrefs_api_key: document.getElementById('ahrefs_api_key').value,
                    openai_api_key: document.getElementById('openai_api_key').value || null,
                    twocaptcha_api_key: document.getElementById('twocaptcha_api_key').value || null,
                    min_domain_rating: parseInt(document.getElementById('min_domain_rating').value),
                    min_organic_traffic: parseInt(document.getElementById('min_organic_traffic').value),
                    max_external_links: parseInt(document.getElementById('max_external_links').value),
                    exclude_subdomains: document.getElementById('exclude_subdomains').value === 'true',
                    max_threads: parseInt(document.getElementById('max_threads').value),
                    sites_per_type: parseInt(document.getElementById('sites_per_type').value),
                    target_site_types: Array.from(document.getElementById('target_site_types').selectedOptions).map(option => option.value)
                };
                
                // Send API request
                fetch('/campaigns/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': apiKey
                    },
                    body: JSON.stringify(data)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('API request failed: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    // Hide loading spinner
                    document.getElementById('newCampaignLoading').style.display = 'none';
                    
                    // Show result
                    document.getElementById('campaignId').textContent = data.campaign_id;
                    document.getElementById('newCampaignResult').style.display = 'block';
                    
                    // Auto-fill the status form
                    document.getElementById('status_campaign_id').value = data.campaign_id;
                    document.getElementById('results_campaign_id').value = data.campaign_id;
                })
                .catch(error => {
                    // Hide loading spinner
                    document.getElementById('newCampaignLoading').style.display = 'none';
                    
                    // Show error
                    showError('newCampaignError', 'Error starting campaign: ' + error.message);
                });
            }
            
            // Check campaign status
            function checkStatus() {
                // Hide previous results and errors
                document.getElementById('campaignStatus').style.display = 'none';
                document.getElementById('statusError').style.display = 'none';
                
                // Show loading spinner
                document.getElementById('statusLoading').style.display = 'block';
                
                const campaignId = document.getElementById('status_campaign_id').value;
                
                // Send API request
                fetch(`/campaigns/${campaignId}/status`, {
                    method: 'GET',
                    headers: {
                        'X-API-Key': apiKey
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('API request failed: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    // Hide loading spinner
                    document.getElementById('statusLoading').style.display = 'none';
                    
                    // Show result
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('campaignStatus').style.display = 'block';
                })
                .catch(error => {
                    // Hide loading spinner
                    document.getElementById('statusLoading').style.display = 'none';
                    
                    // Show error
                    showError('statusError', 'Error checking status: ' + error.message);
                });
            }
            
            // View campaign results
            function viewResults() {
                // Hide previous results and errors
                document.getElementById('campaignResults').style.display = 'none';
                document.getElementById('resultsError').style.display = 'none';
                
                // Show loading spinner
                document.getElementById('resultsLoading').style.display = 'block';
                
                const campaignId = document.getElementById('results_campaign_id').value;
                
                // Send API request
                fetch(`/campaigns/${campaignId}/results`, {
                    method: 'GET',
                    headers: {
                        'X-API-Key': apiKey
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('API request failed: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    // Hide loading spinner
                    document.getElementById('resultsLoading').style.display = 'none';
                    
                    // Format and display results
                    let resultsHtml = `
                        <p><strong>Status:</strong> ${data.status}</p>
                    `;
                    
                    if (data.results) {
                        resultsHtml += `
                            <p><strong>Quality Sites Found:</strong> ${data.results.quality_sites_found}</p>
                            <p><strong>Submissions Attempted:</strong> ${data.results.submissions_attempted}</p>
                            <p><strong>Successful Submissions:</strong> ${data.results.successful_submissions}</p>
                            <p><strong>Failed Submissions:</strong> ${data.results.failed_submissions}</p>
                        `;
                        
                        if (data.results.results_by_site_type) {
                            resultsHtml += `<h4>Results by Site Type</h4><table>
                                <tr>
                                    <th>Site Type</th>
                                    <th>Sites Found</th>
                                    <th>Successful</th>
                                    <th>Failed</th>
                                </tr>`;
                                
                            for (const [siteType, typeResults] of Object.entries(data.results.results_by_site_type)) {
                                resultsHtml += `<tr>
                                    <td>${siteType}</td>
                                    <td>${typeResults.sites_found}</td>
                                    <td>${typeResults.successful_submissions}</td>
                                    <td>${typeResults.failed_submissions}</td>
                                </tr>`;
                            }
                            
                            resultsHtml += `</table>`;
                        }
                    } else {
                        resultsHtml += `<p>No results available yet.</p>`;
                    }
                    
                    document.getElementById('resultsContent').innerHTML = resultsHtml;
                    document.getElementById('campaignResults').style.display = 'block';
                })
                .catch(error => {
                    // Hide loading spinner
                    document.getElementById('resultsLoading').style.display = 'none';
                    
                    // Show error
                    showError('resultsError', 'Error fetching results: ' + error.message);
                });
            }
            
            // Helper function to show errors
            function showError(elementId, message) {
                const element = document.getElementById(elementId);
                element.textContent = message;
                element.style.display = 'block';
            }
        });
    </script>
</body>
</html>""")

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
if API_KEY == "your-default-api-key":
    logger.warning("Using default API key. Consider setting a secure API key using the API_KEY environment variable.")

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
    min_domain_rating: int = Field(50, ge=0, le=100, description="Minimum domain rating (0-100)")
    min_organic_traffic: int = Field(500, ge=0, description="Minimum organic traffic")
    max_external_links: int = Field(100, ge=0, description="Maximum external links")
    exclude_subdomains: bool = True
    max_threads: int = Field(3, ge=1, le=10, description="Maximum concurrent threads (1-10)")
    sites_per_type: int = Field(3, ge=1, le=20, description="Number of sites per type (1-20)")
    target_site_types: List[str] = ["forums", "blogs", "qa_sites", "directories", "social_bookmarks"]
    sites_data: Dict[str, SiteConfig] = {}

# Run campaign in the background
def run_campaign_task(campaign_id: str, config: CampaignConfig):
    try:
        campaign_status[campaign_id] = "running"
        logger.info(f"Starting campaign {campaign_id}")
        
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
        logger.info(f"Campaign {campaign_id} completed successfully")
        
        # Cleanup
        link_builder.cleanup()
        del active_campaigns[campaign_id]
        
    except Exception as e:
        logger.error(f"Campaign error: {str(e)}", exc_info=True)
        campaign_status[campaign_id] = f"failed: {str(e)}"
        
        # Cleanup if link builder was created
        if campaign_id in active_campaigns:
            try:
                active_campaigns[campaign_id].cleanup()
                del active_campaigns[campaign_id]
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}", exc_info=True)

# Routes for the UI
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return templates.TemplateResponse("index.html", {"request": {}})

# API Endpoints
@app.post("/campaigns/", status_code=202, dependencies=[Depends(verify_api_key)])
async def start_campaign(config: CampaignConfig, background_tasks: BackgroundTasks):
    """Start a new link building campaign."""
    campaign_id = f"campaign_{int(time.time())}"
    logger.info(f"Received request to start campaign {campaign_id}")
    
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
            logger.info(f"Campaign {campaign_id} cancelled")
            return {"campaign_id": campaign_id, "status": "cancelled"}
        except Exception as e:
            logger.error(f"Error cancelling campaign: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error cancelling campaign: {str(e)}")
    else:
        return {"campaign_id": campaign_id, "status": campaign_status[campaign_id]}

@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Error handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

# Run the app if this file is executed directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
