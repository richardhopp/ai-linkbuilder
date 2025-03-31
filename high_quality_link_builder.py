import requests
import time
import json
import random
import logging
import re
import string
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import openai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from twocaptcha import TwoCaptcha
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import pandas as pd


class HighQualityLinkBuilder:
    def __init__(self, config_file="config.json"):
        """Initialize the link builder with configuration settings."""
        self.load_config(config_file)
        self.setup_logging()
        self.setup_driver()
        self.setup_nlp()
        self.setup_2captcha()
        self.successful_submissions = 0
        self.failed_submissions = 0
        self.sites_data = {
            "Living Abroad - Aparthotels": {
                "url": "https://aparthotel.com",
                "description": "Offers aparthotels, rental options, and travel guides for local living.",
                "keywords": ["aparthotel", "rental", "travel", "accommodation", "temporary housing", 
                            "expatriate", "digital nomad", "extended stay", "vacation rental", "furnished"]
            },
            "Crypto Rentals": {
                "url": "https://cryptoapartments.com",
                "description": "Modern rental platform accepting cryptocurrency with travel and lifestyle insights.",
                "keywords": ["cryptocurrency", "bitcoin", "ethereum", "rental", "blockchain", 
                            "digital currency", "crypto payment", "travel", "modern living", "tech"]
            },
            "Serviced Apartments": {
                "url": "https://servicedapartments.net",
                "description": "Specializes in serviced apartments with travel tips and local renting rules.",
                "keywords": ["serviced apartment", "temporary housing", "corporate housing", "short-term rental", 
                            "business travel", "relocation", "housekeeping", "concierge", "amenities"]
            },
            "Furnished Apartments": {
                "url": "https://furnishedapartments.net",
                "description": "Focuses on furnished apartments with immediate living solutions and local analysis.",
                "keywords": ["furnished apartment", "ready to move", "turnkey", "fully equipped", 
                            "move-in ready", "short-term rental", "temporary housing", "home essentials"]
            },
            "Real Estate Abroad": {
                "url": "https://realestateabroad.com",
                "description": "International property investments, buying guides, financing tips, and market analysis.",
                "keywords": ["international real estate", "overseas property", "foreign investment", 
                            "global real estate", "international property market", "overseas buying guide"]
            },
            "Property Developments": {
                "url": "https://propertydevelopments.com",
                "description": "Latest new property projects with detailed buying and financing guides.",
                "keywords": ["property development", "new construction", "pre-construction", "real estate project", 
                            "off-plan property", "construction investment", "new build", "property launch"]
            },
            "Property Investment": {
                "url": "https://propertyinvestment.net",
                "description": "Dedicated to property investment with how-to articles, financing guides, and yield analysis.",
                "keywords": ["property investment", "real estate investment", "rental yield", "ROI", 
                            "capital appreciation", "investment strategy", "passive income", "property portfolio"]
            },
            "Golden Visa Opportunities": {
                "url": "https://golden-visa.com",
                "description": "Focuses on Golden Visa properties and investment immigration for the global elite.",
                "keywords": ["golden visa", "investment visa", "investor visa", "residency by investment", 
                            "european residency", "portugal golden visa", "spain golden visa", "greece golden visa"]
            },
            "Residence by Investment": {
                "url": "https://residence-by-investment.com",
                "description": "Guides investors on obtaining residency through property investments across markets.",
                "keywords": ["residence by investment", "residency program", "permanent residency", 
                            "investment migration", "second residency", "residency permit", "property investment"]
            },
            "Citizenship by Investment": {
                "url": "https://citizenship-by-investment.net",
                "description": "Covers citizenship-by-investment programs with global insights and investment tips.",
                "keywords": ["citizenship by investment", "second passport", "economic citizenship", 
                            "dual citizenship", "caribbean citizenship", "investor citizenship", "global mobility"]
            }
        }
        
    def load_config(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Default configuration
            self.config = {
                "ahrefs_api_key": "",
                "openai_api_key": "",
                "twocaptcha_api_key": "",
                "min_domain_rating": 50,
                "min_organic_traffic": 500,
                "max_external_links": 100,
                "exclude_subdomains": True,
                "max_threads": 5,
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
                ],
                "target_site_types": ["forums", "blogs", "qa_sites", "directories", "social_bookmarks", "wiki_sites", "comment_sections"],
                "submission_delay": {
                    "min": 15,
                    "max": 45
                },
                "smart_linking": {
                    "links_per_post": {
                        "min": 1,
                        "max": 2
                    },
                    "anchor_text_variation": True,
                    "contextual_relevance_threshold": 0.6
                },
                "proxy_list": []
            }
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                
    def setup_logging(self):
        """Configure logging."""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = f"{log_dir}/link_builder_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("HighQualityLinkBuilder")
        
    def setup_driver(self):
        """Setup Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add additional preferences to make detection harder
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        if self.config.get("proxy_list"):
            proxy = random.choice(self.config["proxy_list"])
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        user_agent = random.choice(self.config["user_agents"])
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
    def setup_nlp(self):
        """Set up Natural Language Processing tools."""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stopwords = set(stopwords.words('english'))
            
            # Set up OpenAI for advanced content generation
            if self.config.get("openai_api_key"):
                openai.api_key = self.config["openai_api_key"]
            else:
                self.logger.warning("No OpenAI API key provided. Using basic text generation instead.")
                
        except Exception as e:
            self.logger.error(f"Error setting up NLP: {str(e)}")
            
    def setup_2captcha(self):
        """Set up 2Captcha solver."""
        if self.config.get("twocaptcha_api_key"):
            self.solver = TwoCaptcha(self.config["twocaptcha_api_key"])
        else:
            self.logger.warning("No 2Captcha API key provided. CAPTCHA solving will be limited.")
            
    def solve_recaptcha(self, site_key, site_url):
        """
        Solve reCAPTCHA using 2Captcha service.
        Returns the g-recaptcha-response token.
        """
        try:
            if not hasattr(self, 'solver'):
                self.logger.error("2Captcha solver not initialized")
                return None
                
            self.logger.info(f"Solving reCAPTCHA for {site_url} with site key {site_key}")
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=site_url
            )
            
            return result.get('code')
            
        except Exception as e:
            self.logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return None
            
    def solve_image_captcha(self, image_url=None, image_base64=None):
        """
        Solve image-based CAPTCHA using 2Captcha service.
        Accepts either image URL or base64-encoded image data.
        """
        try:
            if not hasattr(self, 'solver'):
                self.logger.error("2Captcha solver not initialized")
                return None
                
            if image_url:
                self.logger.info(f"Solving image CAPTCHA from URL: {image_url}")
                result = self.solver.normal(image_url)
            elif image_base64:
                self.logger.info("Solving image CAPTCHA from base64 data")
                result = self.solver.normal(image_base64)
            else:
                self.logger.error("No image data provided for CAPTCHA solving")
                return None
                
            return result.get('code')
            
        except Exception as e:
            self.logger.error(f"Error solving image CAPTCHA: {str(e)}")
            return None
            
    def detect_captcha(self):
        """Detect and handle various types of CAPTCHAs."""
        try:
            # Look for reCAPTCHA v2
            recaptcha_box = self.driver.find_elements(By.CSS_SELECTOR, ".g-recaptcha")
            if recaptcha_box:
                site_key = recaptcha_box[0].get_attribute("data-sitekey")
                if site_key:
                    # Get the current URL
                    current_url = self.driver.current_url
                    
                    # Solve reCAPTCHA
                    g_response = self.solve_recaptcha(site_key, current_url)
                    if g_response:
                        # Execute JavaScript to set the response
                        self.driver.execute_script(
                            f'document.getElementById("g-recaptcha-response").innerHTML="{g_response}";'
                        )
                        return True
                        
            # Look for image CAPTCHA
            img_captchas = self.driver.find_elements(By.XPATH, 
                "//img[contains(@src, 'captcha') or contains(@class, 'captcha') or contains(@id, 'captcha')]")
            
            if img_captchas:
                img_src = img_captchas[0].get_attribute("src")
                if img_src:
                    # Solve image CAPTCHA
                    captcha_text = self.solve_image_captcha(image_url=img_src)
                    if captcha_text:
                        # Find the input field for the CAPTCHA
                        captcha_input = self.driver.find_element(By.XPATH, 
                            "//input[contains(@name, 'captcha') or contains(@id, 'captcha')]")
                        captcha_input.send_keys(captcha_text)
                        return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting/handling CAPTCHA: {str(e)}")
            return False
            
    def submit_to_directory(self, url):
        """Submit to a web directory."""
        try:
            self.driver.get(url)
            
            # For directories, we pick a relevant site from our money sites
            # Extract page topic to match
            _, _, topic = self.extract_page_context(url, "directories")
            
            # Generate content and select site
            content, site_info = self.generate_smart_content("directories", url, None, None, topic)
            
            # Look for submission form
            submission_links = None
            submission_patterns = ["submit", "add", "suggest", "add site", "add url", "add listing"]
            
            for pattern in submission_patterns:
                try:
                    links = self.driver.find_elements(By.XPATH, 
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]")
                    
                    if links:
                        links[0].click()
                        time.sleep(3)  # Wait for form page to load
                        break
                except:
                    continue
                    
            # Now look for form fields
            form_found = False
            
            # Look for URL field first (most important)
            url_fields = self.driver.find_elements(By.XPATH, 
                "//input[contains(@name, 'url') or contains(@id, 'url') or contains(@name, 'website') or contains(@id, 'website')]")
            
            if url_fields:
                url_fields[0].send_keys(site_info["url"])
                form_found = True
                
                # Look for title/name field
                title_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@name, 'title') or contains(@id, 'title') or contains(@name, 'name') or contains(@id, 'name')]")
                
                if title_fields:
                    title_fields[0].send_keys(site_info["name"])
                    
                # Look for description field
                desc_fields = self.driver.find_elements(By.XPATH, 
                    "//textarea[contains(@name, 'desc') or contains(@id, 'desc') or contains(@name, 'description') or contains(@id, 'description')]")
                
                if desc_fields:
                    desc_fields[0].send_keys(site_info["description"])
                    
                # Look for category selection
                category_selects = self.driver.find_elements(By.XPATH, "//select[contains(@name, 'category') or contains(@id, 'category')]")
                if category_selects:
                    # Find real estate or travel related options
                    select = category_selects[0]
                    options = select.find_elements(By.TAG_NAME, "option")
                    
                    category_keywords = ["real estate", "property", "travel", "housing", "accommodation", "investment"]
                    for option in options:
                        option_text = option.text.lower()
                        for keyword in category_keywords:
                            if keyword in option_text:
                                option.click()
                                break
                                
                # Look for email field
                email_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@name, 'email') or contains(@id, 'email')]")
                
                if email_fields:
                    email = f"contact{self.generate_random_string(6)}@example.com"
                    email_fields[0].send_keys(email)
                    
                # Handle CAPTCHA if present
                self.detect_captcha()
                
                # Find and click submit button
                submit_buttons = self.driver.find_elements(By.XPATH, 
                    "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Submit') or contains(text(), 'Add')]")
                
                if submit_buttons:
                    # In actual use, uncomment this to submit
                    # submit_buttons[0].click()
                    self.logger.info(f"Directory submission prepared at {url} for {site_info['url']}")
                    return True
                    
            if not form_found:
                self.logger.warning(f"Could not find submission form on directory: {url}")
                
            return form_found
            
        except Exception as e:
            self.logger.error(f"Error submitting to directory {url}: {str(e)}")
            return False
            
    def submit_to_wiki(self, url):
        """Submit content to a wiki site."""
        try:
            self.driver.get(url)
            
            # Extract context for content generation
            context_text, _, topic = self.extract_page_context(url, "wiki_sites")
            
            # Generate smart content
            content, site_info = self.generate_smart_content("wiki_sites", url, context_text, None, topic)
            
            # Look for edit links
            edit_links = None
            edit_patterns = ["edit", "edit page", "modify", "contribute"]
            
            for pattern in edit_patterns:
                try:
                    links = self.driver.find_elements(By.XPATH, 
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]")
                    
                    if links:
                        links[0].click()
                        time.sleep(3)  # Wait for edit page to load
                        break
                except:
                    continue
                    
            # Look for edit area
            edit_area = None
            edit_selectors = [
                "//textarea[@id='wpTextbox1']",  # MediaWiki
                "//textarea[contains(@class, 'editor')]",
                "//div[@contenteditable='true']"
            ]
            
            for selector in edit_selectors:
                try:
                    edit_elements = self.driver.find_elements(By.XPATH, selector)
                    if edit_elements:
                        edit_area = edit_elements[0]
                        break
                except:
                    continue
                    
            if edit_area:
                # For wikis, we need to be careful - usually append rather than replace
                current_text = edit_area.get_attribute("value") or edit_area.text
                
                # Find a good place to insert our content
                if current_text:
                    # Find a relevant section to add to
                    sections = re.split(r'==+\s*[\w\s]+\s*==+', current_text)
                    if len(sections) > 1:
                        # Find most relevant section
                        best_section_index = 0
                        best_match_score = 0
                        
                        for i, section in enumerate(sections):
                            if not section.strip():
                                continue
                                
                            # Simple relevance scoring
                            score = 0
                            for keyword in site_info["keywords"]:
                                if keyword.lower() in section.lower():
                                    score += 1
                                    
                            if score > best_match_score:
                                best_match_score = score
                                best_section_index = i
                                
                        # Append to best section
                        sections[best_section_index] += "\n\n" + content
                        
                        # Reconstruct the text with section headers
                        new_text = ""
                        section_headers = re.findall(r'(==+\s*[\w\s]+\s*==+)', current_text)
                        for i in range(len(sections)):
                            if i > 0 and i-1 < len(section_headers):
                                new_text += section_headers[i-1]
                            new_text += sections[i]
                            
                        # Set the new text
                        if edit_area.tag_name.lower() == "div":
                            self.driver.execute_script("arguments[0].innerHTML = arguments[1]", edit_area, new_text)
                        else:
                            edit_area.clear()
                            edit_area.send_keys(new_text)
                    else:
                        # Just append to end
                        if edit_area.tag_name.lower() == "div":
                            self.driver.execute_script(
                                "arguments[0].innerHTML = arguments[0].innerHTML + arguments[1]", 
                                edit_area, 
                                "<p>" + content + "</p>"
                            )
                        else:
                            edit_area.send_keys("\n\n" + content)
                else:
                    # Empty wiki page
                    edit_area.send_keys(content)
                    
                # Look for summary/comment field
                summary_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@id, 'summary') or contains(@name, 'summary') or contains(@id, 'comment') or contains(@name, 'comment')]")
                
                if summary_fields:
                    summary_fields[0].send_keys("Added information about " + site_info["keywords"][0])
                    
                # Handle CAPTCHA if present
                self.detect_captcha()
                
                # Find and click submit button
                submit_buttons = self.driver.find_elements(By.XPATH, 
                    "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Save') or contains(text(), 'Submit') or contains(text(), 'Publish')]")
                
                if submit_buttons:
                    # In actual use, uncomment this to submit
                    # submit_buttons[0].click()
                    self.logger.info(f"Wiki edit prepared at {url} linking to {site_info['url']}")
                    return True
                    
            self.logger.warning(f"Could not find edit area on wiki: {url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting to wiki {url}: {str(e)}")
            return False
            
    def submit_to_social_bookmark(self, url):
        """Submit to a social bookmarking site."""
        try:
            self.driver.get(url)
            
            # For social bookmarks, we should pick the most relevant site from our money sites
            _, _, topic = self.extract_page_context(url, "social_bookmarks")
            
            # Generate content and select site
            content, site_info = self.generate_smart_content("social_bookmarks", url, None, None, topic)
            
            # Look for submission form
            submit_links = None
            submit_patterns = ["submit", "add", "post", "share", "bookmark"]
            
            for pattern in submit_patterns:
                try:
                    links = self.driver.find_elements(By.XPATH, 
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]")
                    
                    if links:
                        links[0].click()
                        time.sleep(3)  # Wait for form page to load
                        break
                except:
                    continue
                    
            # Look for URL field
            url_fields = self.driver.find_elements(By.XPATH, 
                "//input[contains(@name, 'url') or contains(@id, 'url') or contains(@placeholder, 'http') or contains(@type, 'url')]")
            
            if url_fields:
                url_fields[0].send_keys(site_info["url"])
                
                # Look for title field
                title_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@name, 'title') or contains(@id, 'title') or contains(@name, 'name') or contains(@id, 'name')]")
                
                if title_fields:
                    title_fields[0].send_keys(site_info["name"])
                    
                # Look for description field
                desc_fields = self.driver.find_elements(By.XPATH, 
                    "//textarea[contains(@name, 'desc') or contains(@id, 'desc') or contains(@name, 'description') or contains(@id, 'description')]")
                
                if desc_fields:
                    desc_fields[0].send_keys(site_info["description"])
                    
                # Look for tags field
                tags_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@name, 'tag') or contains(@id, 'tag') or contains(@name, 'tags') or contains(@id, 'tags')]")
                
                if tags_fields:
                    # Use 3-5 relevant keywords as tags
                    tags = ", ".join(random.sample(site_info["keywords"], min(5, len(site_info["keywords"]))))
                    tags_fields[0].send_keys(tags)
                    
                # Handle CAPTCHA if present
                self.detect_captcha()
                
                # Find and click submit button
                submit_buttons = self.driver.find_elements(By.XPATH, 
                    "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Submit') or contains(text(), 'Save') or contains(text(), 'Add')]")
                
                if submit_buttons:
                    # In actual use, uncomment this to submit
                    # submit_buttons[0].click()
                    self.logger.info(f"Social bookmark submission prepared at {url} for {site_info['url']}")
                    return True
                    
            self.logger.warning(f"Could not find submission form on social bookmark site: {url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting to social bookmark {url}: {str(e)}")
            return False
            
    def submit_to_comment_section(self, url):
        """Submit to a generic comment section."""
        try:
            self.driver.get(url)
            
            # Extract context for content generation
            context_text, _, topic = self.extract_page_context(url, "comment_sections")
            
            # Generate smart content
            content, site_info = self.generate_smart_content("comment_sections", url, context_text, None, topic)
            
            # Look for comment form - common patterns
            comment_area = None
            comment_selectors = [
                "//textarea[contains(@id, 'comment') or contains(@name, 'comment')]",
                "//div[contains(@class, 'comment-form')]//textarea",
                "//form[contains(@id, 'comment')]//textarea",
                "//div[@contenteditable='true' and contains(@class, 'comment')]"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(By.XPATH, selector)
                    if comment_elements:
                        comment_area = comment_elements[0]
                        break
                except:
                    continue
                    
            if comment_area:
                # Fill in comment text
                if comment_area.tag_name.lower() == "div":
                    self.driver.execute_script("arguments[0].innerHTML = arguments[1]", comment_area, content)
                else:
                    comment_area.send_keys(content)
                    
                # Look for name field
                name_fields = self.driver.find_elements(By.XPATH, 
                    "//input[contains(@id, 'name') or contains(@name, 'name') or contains(@id, 'author') or contains(@name, 'author')]")
                
                if name_fields:
                    name = f"User {self.generate_random_string(6)}"
                    name_fields[0].send_keys(name)
                    
                    # Look for email field
                    email_fields = self.driver.find_elements(By.XPATH, 
                        "//input[contains(@id, 'email') or contains(@name, 'email')]")
                    
                    if email_fields:
                        email = f"{name.replace(' ', '')}@example.com"
                        email_fields[0].send_keys(email)
                        
                        # Look for website/URL field
                        url_fields = self.driver.find_elements(By.XPATH, 
                            "//input[contains(@id, 'url') or contains(@name, 'url') or contains(@id, 'website') or contains(@name, 'website')]")
                        
                        if url_fields:
                            url_fields[0].send_keys(site_info["url"])
                            
                # Handle CAPTCHA if present
                self.detect_captcha()
                
                # Find and click submit button
                submit_buttons = self.driver.find_elements(By.XPATH, 
                    "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Post') or contains(text(), 'Submit') or contains(text(), 'Comment')]")
                
                if submit_buttons:
                    # In actual use, uncomment this to submit
                    # submit_buttons[0].click()
                    self.logger.info(f"Comment prepared at {url} linking to {site_info['url']}")
                    return True
                    
            self.logger.warning(f"Could not find comment form on: {url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting to comment section {url}: {str(e)}")
            return False
            
    def submit_to_site(self, url, site_type):
        """Submit to a site based on its type."""
        try:
            # Add random delay to mimic human behavior
            delay = random.uniform(
                self.config["submission_delay"]["min"],
                self.config["submission_delay"]["max"]
            )
            time.sleep(delay)
            
            # Select submission method based on site type
            if site_type == "forums":
                result = self.submit_to_forum(url)
            elif site_type == "blogs":
                result = self.submit_to_blog(url)
            elif site_type == "qa_sites":
                result = self.submit_to_qa_site(url)
            elif site_type == "directories":
                result = self.submit_to_directory(url)
            elif site_type == "social_bookmarks":
                result = self.submit_to_social_bookmark(url)
            elif site_type == "wiki_sites":
                result = self.submit_to_wiki(url)
            elif site_type == "comment_sections":
                result = self.submit_to_comment_section(url)
            else:
                self.logger.warning(f"Unknown site type: {site_type}")
                return False
                
            if result:
                self.successful_submissions += 1
            else:
                self.failed_submissions += 1
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error submitting to {url}: {str(e)}")
            self.failed_submissions += 1
            return False
            
    def run_campaign(self, sites_per_type=5):
        """Run a full link building campaign."""
        self.logger.info("Starting high-quality link building campaign")
        
        # Load sites data from the dictionary we initialized
        if not self.sites_data:
            self.logger.error("No sites data found. Aborting campaign.")
            return
            
        # Track overall statistics
        total_quality_sites_found = 0
        total_submissions_attempted = 0
        
        for site_type in self.config["target_site_types"]:
            self.logger.info(f"Finding {site_type} sites...")
            sites = self.find_submission_sites(site_type, sites_per_type)
            
            total_quality_sites_found += len(sites)
            self.logger.info(f"Found {len(sites)} quality {site_type} sites meeting criteria (DR50+, 500+ traffic, <100 external links)")
            
            if sites:
                self.logger.info(f"Attempting submissions to {len(sites)} {site_type} sites...")
                
                # Use ThreadPoolExecutor for parallel submissions if configured
                if self.config["max_threads"] > 1:
                    with ThreadPoolExecutor(max_workers=self.config["max_threads"]) as executor:
                        results = list(executor.map(lambda url: self.submit_to_site(url, site_type), sites))
                        total_submissions_attempted += len(results)
                else:
                    # Sequential processing
                    for url in sites:
                        self.submit_to_site(url, site_type)
                        total_submissions_attempted += 1
                        
        # Log final statistics
        self.logger.info(f"Campaign completed.")
        self.logger.info(f"Quality sites found: {total_quality_sites_found}")
        self.logger.info(f"Submissions attempted: {total_submissions_attempted}")
        self.logger.info(f"Successful submissions: {self.successful_submissions}")
        self.logger.info(f"Failed submissions: {self.failed_submissions}")
        
        # Return campaign results
        return {
            "quality_sites_found": total_quality_sites_found,
            "submissions_attempted": total_submissions_attempted,
            "successful_submissions": self.successful_submissions,
            "failed_submissions": self.failed_submissions
        }
        
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


if __name__ == "__main__":
    # Example usage
    link_builder = HighQualityLinkBuilder()
    try:
        # Set your API keys
        link_builder.config["ahrefs_api_key"] = "YOUR_AHREFS_API_KEY"
        link_builder.config["openai_api_key"] = "YOUR_OPENAI_API_KEY"  # Optional but recommended
        link_builder.config["twocaptcha_api_key"] = "YOUR_2CAPTCHA_API_KEY"  # Optional but recommended
        
        # Configure quality thresholds
        link_builder.config["min_domain_rating"] = 50  # Minimum DR 50
        link_builder.config["min_organic_traffic"] = 500  # Minimum 500 traffic
        link_builder.config["max_external_links"] = 100  # Maximum 100 external links
        link_builder.config["exclude_subdomains"] = True  # Exclude subdomains
        
        # Run the campaign
        results = link_builder.run_campaign(sites_per_type=3)
        print(f"Campaign Results: {results}")
    except Exception as e:
        link_builder.logger.error(f"Error detecting/handling CAPTCHA: {str(e)}")
    finally:
        link_builder.cleanup()

def check_site_quality(self, domain, url=None):
    """
    Check site quality using Ahrefs API v3.
    Returns True if the site meets quality criteria, False otherwise.
    """
    if not self.config["ahrefs_api_key"]:
        self.logger.warning("No Ahrefs API key provided. Skipping quality check.")
        return True
    
    # Remove www. if present
        clean_domain = domain.replace("www.", "")
        
        # Exclude subdomains if configured
        if self.config["exclude_subdomains"]:
            parts = clean_domain.split('.')
            if len(parts) > 2:
                self.logger.info(f"Skipping subdomain: {domain}")
                return False
                
        api_url = "https://api.ahrefs.com/v3/site-explorer/overview"
        
        headers = {
            "Authorization": f"Bearer {self.config['ahrefs_api_key']}",
            "Content-Type": "application/json"
        }
        
        params = {
            "target": clean_domain,
            "protocol": "both"
        }
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            data = response.json()
            
            if response.status_code != 200:
                error_message = data.get('error', {}).get('message', 'Unknown error')
                self.logger.error(f"Ahrefs API error: {error_message}")
                return False
                
            domain_rating = data.get("metrics", {}).get("domain_rating", 0)
            organic_traffic = data.get("metrics", {}).get("organic", {}).get("traffic", 0)
            
            self.logger.info(f"Domain: {domain}, DR: {domain_rating}, Traffic: {organic_traffic}")
            
            # Check if domain meets basic quality criteria
            if (domain_rating >= self.config["min_domain_rating"] and 
                organic_traffic >= self.config["min_organic_traffic"]):
                
                # If URL is provided, check external links count
                if url:
                    external_links_count = self.check_external_links_count(clean_domain, url)
                    if external_links_count is None or external_links_count <= self.config["max_external_links"]:
                        return True
                    else:
                        self.logger.info(f"Too many external links ({external_links_count}) on {url}")
                        return False
                else:
                    return True
            else:
                self.logger.info(f"Domain {domain} doesn't meet quality criteria (DR: {domain_rating}, Traffic: {organic_traffic})")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking site quality for {domain}: {str(e)}")
            return False
            
    def check_external_links_count(self, domain, url):
        """
        Check the number of external links on a specific URL using Ahrefs API v3.
        Returns the count or None if unavailable.
        """
        api_url = "https://api.ahrefs.com/v3/site-explorer/linked-domains-from-page"
        
        headers = {
            "Authorization": f"Bearer {self.config['ahrefs_api_key']}",
            "Content-Type": "application/json"
        }
        
        params = {
            "target": url,
            "protocol": "both",
            "limit": 1  # We only need the count
        }
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            data = response.json()
            
            if response.status_code != 200:
                error_message = data.get('error', {}).get('message', 'Unknown error')
                self.logger.error(f"Ahrefs API error when checking external links: {error_message}")
                return None
                
            # Get count of external domains linked from this page
            count = data.get("count", 0)
            return count
            
        except Exception as e:
            self.logger.error(f"Error checking external links for {url}: {str(e)}")
            return None
            
    def generate_smart_content(self, site_type, target_url, context_text=None, question=None, topic=None):
        """
        Generate relevant content based on target site type and available context.
        Returns tuple of (content, relevant_site)
        """
        try:
            # Extract domain and page topic
            domain = urlparse(target_url).netloc
            page_topic = topic if topic else self.extract_page_topic(context_text)
            
            # Select relevant money sites based on topic relevance
            relevant_site = self.select_relevant_site(page_topic)
            
            # Determine number of links to include
            links_count = random.randint(
                self.config["smart_linking"]["links_per_post"]["min"],
                self.config["smart_linking"]["links_per_post"]["max"]
            )
            
            # Generate content based on site type
            if self.config.get("openai_api_key"):
                return self.generate_ai_content(site_type, domain, page_topic, question, context_text, relevant_site, links_count)
            else:
                return self.generate_template_content(site_type, page_topic, question, relevant_site, links_count)
                
        except Exception as e:
            self.logger.error(f"Error generating smart content: {str(e)}")
            return self.generate_fallback_content(site_type, relevant_site)
            
    def extract_page_topic(self, context_text):
        """Extract the main topic from page content."""
        if not context_text:
            return None
            
        try:
            # Tokenize and remove stopwords
            tokens = [w.lower() for w in word_tokenize(context_text) if w.isalpha()]
            filtered_tokens = [w for w in tokens if w not in self.stopwords and len(w) > 3]
            
            # Count word frequencies
            freq_dist = nltk.FreqDist(filtered_tokens)
            top_words = [word for word, freq in freq_dist.most_common(5)]
            
            return " ".join(top_words)
            
        except Exception as e:
            self.logger.error(f"Error extracting page topic: {str(e)}")
            return None
            
    def select_relevant_site(self, topic):
        """
        Select the most relevant money site based on topic.
        Returns dict with site information.
        """
        if not topic:
            # If no topic, select a random site
            site_name = random.choice(list(self.sites_data.keys()))
            return {"name": site_name, **self.sites_data[site_name]}
            
        # Calculate relevance scores for each site
        scores = {}
        topic_tokens = set(topic.lower().split())
        
        for site_name, site_info in self.sites_data.items():
            # Score based on keyword overlap
            keywords = set([k.lower() for k in site_info["keywords"]])
            keyword_overlap = len(topic_tokens.intersection(keywords))
            
            # Add random factor to avoid always picking the same site for similar topics
            random_boost = random.uniform(0, 0.5)
            scores[site_name] = keyword_overlap + random_boost
            
        # Get site with highest score
        if scores:
            best_site_name = max(scores, key=scores.get)
            return {"name": best_site_name, **self.sites_data[best_site_name]}
        else:
            # Fallback to random selection
            site_name = random.choice(list(self.sites_data.keys()))
            return {"name": site_name, **self.sites_data[site_name]}
            
    def generate_ai_content(self, site_type, domain, page_topic, question, context_text, site_info, links_count):
        """Generate content using OpenAI."""
        try:
            prompt_content = ""
            
            if site_type == "forums":
                prompt_content = f"""Write a helpful, informative forum post about {page_topic if page_topic else 'living abroad or real estate investment'}. 
                The forum is on {domain}. Make it sound natural and conversational, not promotional.
                Incorporate {links_count} natural reference(s) to {site_info['url']} which specializes in {site_info['description']}
                Do not use obvious promotional language. Make the link relevant to the discussion.
                Response should be 3-4 paragraphs and include a question at the end to encourage replies."""
                
            elif site_type == "blogs":
                prompt_content = f"""Write a thoughtful blog comment about {page_topic if page_topic else 'property investment or living abroad'}. 
                The blog is on {domain}. Be insightful and add value to the article.
                Naturally incorporate {links_count} reference(s) to {site_info['url']} which offers {site_info['description']}
                Avoid obvious promotional language. Make the links feel helpful in context.
                Response should be 2-3 paragraphs, conversational but intelligent."""
                
            elif site_type == "qa_sites":
                if question:
                    prompt_content = f"""Write a detailed, helpful answer to the question: "{question}" 
                    The Q&A site is {domain}. Be informative and thorough.
                    Naturally incorporate {links_count} reference(s) to {site_info['url']} which provides {site_info['description']}
                    Make the link(s) genuinely helpful to someone with this question. Avoid promotional language.
                    Response should be comprehensive yet concise, about 3-4 paragraphs."""
                else:
                    prompt_content = f"""Write a detailed answer about {page_topic if page_topic else 'real estate investment or living abroad'}. 
                    The Q&A site is {domain}. Be informative and thorough.
                    Naturally incorporate {links_count} reference(s) to {site_info['url']} which provides {site_info['description']}
                    Make the link(s) genuinely helpful. Avoid promotional language.
                    Response should be comprehensive yet concise, about 3-4 paragraphs."""
                    
            elif site_type == "comment_sections":
                prompt_content = f"""Write an insightful comment for an article about {page_topic if page_topic else 'property or travel'}. 
                The website is {domain}. Be thoughtful and add to the discussion.
                Subtly incorporate {links_count} reference(s) to {site_info['url']} which focuses on {site_info['description']}
                Make the comment primarily valuable, with the link appearing natural and helpful.
                Response should be 2 paragraphs, intelligent but conversational."""
                
            else:  # Default for other site types
                prompt_content = f"""Write helpful content about {page_topic if page_topic else 'real estate investment or living abroad'} for {domain}.
                Naturally incorporate {links_count} reference(s) to {site_info['url']} which specializes in {site_info['description']}
                Avoid obvious promotional language. Make the content helpful and the links contextually relevant.
                Response should be 2-3 paragraphs, informative and well-written."""
                
            # Add context if available
            if context_text:
                context_sample = context_text[:500] + "..." if len(context_text) > 500 else context_text
                prompt_content += f"\n\nContext from the page: \"{context_sample}\""
                
            # Generate content with OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in real estate, travel, and expatriate living. Write helpful, natural-sounding content that subtly incorporates links without appearing promotional. The links should feel like genuine resources rather than advertisements."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Add HTML link if not already included
            if site_info["url"] not in content:
                # Generate anchor text variations
                anchor_options = [
                    site_info["name"],
                    "this resource",
                    "this helpful site",
                    "this guide",
                    "more information here",
                    random.choice(site_info["keywords"])
                ]
                
                anchor_text = random.choice(anchor_options)
                html_link = f'<a href="{site_info["url"]}">{anchor_text}</a>'
                
                # Insert link at a natural position
                sentences = sent_tokenize(content)
                if len(sentences) > 2:
                    insert_position = random.randint(1, len(sentences) - 2)
                    sentences[insert_position] = sentences[insert_position].replace(
                        anchor_text, html_link) if anchor_text in sentences[insert_position] else \
                        sentences[insert_position] + f" You can find {html_link} for more details."
                    content = " ".join(sentences)
                else:
                    content += f" For more information, check out {html_link}."
                    
            return content, site_info
            
        except Exception as e:
            self.logger.error(f"Error generating AI content: {str(e)}")
            return self.generate_fallback_content(site_type, site_info)
            
    def generate_template_content(self, site_type, page_topic, question, site_info, links_count):
        """Generate content from templates when AI generation is unavailable."""
        try:
            templates = {
                "forums": [
                    "I've been researching {topic} extensively lately. One aspect that really stood out to me was how {site_desc}. I found {site_url} to be particularly helpful for understanding this better. Has anyone else had experience with this? What were your findings?",
                    "Recently moved abroad and been dealing with {topic}. It's been quite the journey! For anyone interested, {site_url} has some really useful information about {site_keywords}. What's everyone else's experience been like?",
                    "Question for the community about {topic} - has anyone found good resources for this? After some research, I came across {site_url} which covers {site_desc} in detail. Curious if others have recommendations too?"
                ],
                "blogs": [
                    "Really enjoyed this post about {topic}! It reminds me of some research I was doing recently. For anyone interested in going deeper on this subject, {site_url} has some complementary information about {site_keywords}. Thanks for sharing your insights!",
                    "Great article! I've been dealing with {topic} myself recently. Found that {site_url} offers some practical advice on {site_desc} that complements what you've written here. Looking forward to more content like this!",
                    "This is exactly what I needed to read today. I've been working on {topic} and found the information at {site_url} about {site_keywords} to be really helpful alongside your insights. Thanks for putting this together!"
                ],
                "qa_sites": [
                    "Based on my experience with {topic}, there are several approaches you could take. First, consider how {site_desc}. You can find more detailed guidance at {site_url} which covers this extensively. Hope this helps!",
                    "To answer your question about {question_text}: The key thing to understand is how {site_desc}. There's a comprehensive guide at {site_url} that I found really clarified the process. Let me know if you need any clarification!",
                    "Having dealt with {topic} myself, I'd recommend first looking into how {site_keywords} work together. {site_url} has some excellent resources that walk through this step by step. The main things to keep in mind are..."
                ],
                "comment_sections": [
                    "This article raises some interesting points about {topic}. From my experience, understanding {site_desc} can add valuable context. I found some helpful insights on this at {site_url}. Thanks for starting this discussion!",
                    "Really appreciate this perspective on {topic}. It connects well with some research I was reading about {site_keywords} recently. For anyone interested in exploring this further, {site_url} offers some complementary information.",
                    "Fascinating read! I've been following developments in {topic} for a while. The relationship between this and {site_desc} is particularly interesting. There's some good analysis of this connection at {site_url}."
                ],
                "default": [
                    "I've found {topic} to be increasingly important lately. Understanding how {site_desc} can make a significant difference. {site_url} offers some valuable resources on this that I've found helpful.",
                    "When dealing with {topic}, it's worth considering how {site_keywords} factor into the equation. There's a helpful overview at {site_url} that covers {site_desc} in detail.",
                    "For anyone interested in {topic}, I would recommend exploring how {site_desc}. You can find more information at {site_url} which I've found to be a reliable resource."
                ]
            }
            
            template_list = templates.get(site_type, templates["default"])
            template = random.choice(template_list)
            
            # Fill in template
            site_keywords = ", ".join(random.sample(site_info["keywords"], min(3, len(site_info["keywords"]))))
            content = template.format(
                topic=page_topic if page_topic else "real estate investment and living abroad",
                site_url=site_info["url"],
                site_desc=site_info["description"],
                site_keywords=site_keywords,
                question_text=question if question else "this topic"
            )
