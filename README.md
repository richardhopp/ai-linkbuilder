# High-Quality Link Builder

An automated link building tool that focuses exclusively on high-quality sites with strong domain metrics.

## Features

- Only targets sites with DR 50+, 500+ traffic, and <100 external links
- Integrates with Ahrefs API v3 for site quality verification
- Uses 2Captcha for automated CAPTCHA solving
- Generates contextually relevant content using OpenAI
- Intelligently selects the most appropriate money site based on context
- Supports various platforms: forums, blogs, Q&A sites, and more

## Deployment to Render

### Prerequisites

1. A Render account (https://render.com)
2. A GitHub or GitLab repository containing this code

### Deployment Steps

1. Push all code to your repository
2. Log in to your Render dashboard
3. Click "New" and select "Blueprint"
4. Connect your repository
5. Render will automatically detect the `render.yaml` configuration
6. Click "Apply"
7. Wait for the deployment to complete (may take up to 10-15 minutes for the first build)

### After Deployment

1. Once deployed, you'll get a URL for your API service
2. The API key will be automatically generated (find it in Environment variables)
3. Use the API endpoints with your API key to start campaigns

## API Usage

### Start a Campaign

```bash
curl -X POST https://your-render-url.onrender.com/campaigns/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "ahrefs_api_key": "your-ahrefs-api-key",
    "openai_api_key": "your-openai-api-key",
    "twocaptcha_api_key": "your-2captcha-api-key",
    "sites_per_type": 3,
    "target_site_types": ["forums", "blogs", "qa_sites"]
  }'
```

### Check Campaign Status

```bash
curl -X GET https://your-render-url.onrender.com/campaigns/campaign_1234567890/status \
  -H "X-API-Key: your-api-key"
```

### Get Campaign Results

```bash
curl -X GET https://your-render-url.onrender.com/campaigns/campaign_1234567890/results \
  -H "X-API-Key: your-api-key"
```

## Local Development

1. Install Docker
2. Build the Docker image: `docker build -t link-builder .`
3. Run the container: `docker run -p 8000:8000 -e API_KEY=your-api-key link-builder`
4. Access the API at http://localhost:8000

## Customization

Edit the config values in your API request to customize:

- Domain rating threshold
- Traffic requirements
- External link limits
- Target site types
- Number of sites per type
- And more
