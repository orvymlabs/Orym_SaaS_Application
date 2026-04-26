"""
Universal Website Data Fetcher

Fetches products, categories, and site information from ANY website URL.
Supports multiple platforms: WooCommerce, Shopify, WordPress, or custom websites.
Uses web scraping as fallback when no API is available.
"""
import re
import logging
import requests
from typing import Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class UniversalWebsiteFetcher:
    """Fetches data from ANY website using APIs or web scraping."""

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL by ensuring it has a scheme and no trailing slash."""
        if not url:
            return ""
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    @staticmethod
    def detect_platform(base_url: str) -> dict:
        """Detect what platform the website is running."""
        result = {
            "platform": "unknown",
            "is_wordpress": False,
            "is_woocommerce": False,
            "is_shopify": False,
            "detected_endpoints": []
        }

        base_url = base_url.rstrip("/")
        try:
            logger.info(f"Platform detection: Fetching {base_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(base_url, timeout=10, verify=False, headers=headers)
            logger.info(f"Platform detection: {base_url} status code: {resp.status_code}")
            
            if resp.status_code == 200:
                html = resp.text.lower()
                
                # Check headers
                server = resp.headers.get("Server", "").lower()
                if "shopify" in server:
                    result["is_shopify"] = True
                    result["platform"] = "shopify"

                if "shopify" in html or ".myshopify.com" in html or "cdn.shopify.com" in html:
                    result["is_shopify"] = True
                    result["platform"] = "shopify"
                
                if "/wp-content/" in html or "/wp-includes/" in html or "wp-json" in html or "wordpress" in html:
                    result["is_wordpress"] = True
                    result["platform"] = "wordpress"
                
                # Check for WooCommerce specifically
                if "woocommerce" in html or "wc-api" in html or "wc-settings" in html:
                    result["is_woocommerce"] = True
                    result["platform"] = "woocommerce"

                # Proactive endpoint check for WordPress/WooCommerce
                endpoints_to_check = [
                    "/wp-json/",
                    "/wp-json/wc/v3/",
                    "/wp-json/wp/v2/pages",
                    "/shop/",
                    "/products/"
                ]

                for endpoint in endpoints_to_check:
                    try:
                        check_url = f"{base_url}{endpoint}"
                        logger.debug(f"Platform detection: Checking {check_url}")
                        wp_resp = requests.get(check_url, timeout=5, verify=False, headers=headers)
                        if wp_resp.status_code in [200, 401]: # 401 means it exists but needs auth
                            result["detected_endpoints"].append(endpoint)
                            if "wp-json" in endpoint:
                                result["is_wordpress"] = True
                                if "wc/v3" in endpoint:
                                    result["is_woocommerce"] = True
                                    result["platform"] = "woocommerce"
                                elif result["platform"] == "unknown":
                                    result["platform"] = "wordpress"
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Platform detection for {base_url} failed: {e}")
        
        # Final adjustment
        if result["is_woocommerce"]:
            result["platform"] = "woocommerce"
        elif result["is_wordpress"] and result["platform"] == "unknown":
            result["platform"] = "wordpress"
            
        return result

    @staticmethod
    def fetch_site_info(base_url: str) -> dict:
        """Fetch basic site information from any website."""
        info = {
            "site_name": "",
            "site_description": "",
            "about": "",
            "services": [],
            "contact": {},
            "pages": []
        }

        try:
            logger.info(f"🌐 Fetching site info for: {base_url}")
            resp = requests.get(base_url, timeout=12, verify=False, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            logger.info(f"Fetching site info for {base_url}: Status code {resp.status_code}")
            if resp.status_code == 200:
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')
                
                title_tag = soup.find('title')
                if title_tag:
                    info["site_name"] = title_tag.get_text().strip()
                    logger.info(f"Extracted site name: {info['site_name']}")
                
                meta_desc = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
                if meta_desc:
                    info["site_description"] = meta_desc.get('content', '').strip()
                    logger.info(f"Extracted site description (truncated): {info['site_description'][:50]}...")
                
                info["contact"] = UniversalWebsiteFetcher._extract_contact_info(html, soup)
                logger.info(f"Extracted contact info: {info['contact']}")
                info["about"] = UniversalWebsiteFetcher._extract_about_info(html, soup)
                logger.info(f"Extracted about info (truncated): {info['about'][:50]}...")
                info["services"] = UniversalWebsiteFetcher._extract_services(html, soup)
                logger.info(f"Extracted {len(info['services'])} services.")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch site info for {base_url} due to network error: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch site info for {base_url} due to parsing error: {e}")

        return info

    @staticmethod
    def _extract_contact_info(html: str, soup: BeautifulSoup) -> dict:
        contact = {"phone": "", "email": "", "address": "", "hours": ""}
        text = soup.get_text(separator=' ', strip=True)

        # Look for contact section specifically - expanded selectors
        contact_sections = []
        contact_patterns = r'contact|footer|info|address|store|about|team|company|corporate|headquarters|office'
        for tag in soup.find_all(['div', 'section', 'footer', 'address', 'header'], class_=re.compile(contact_patterns, re.I)):
            contact_sections.append(tag.get_text(separator=' ', strip=True))

        # Also look for contact links
        for link in soup.find_all('a', href=re.compile(r'contact|about|tel:|mailto:', re.I)):
            contact_text = link.get_text(strip=True)
            if contact_text and len(contact_text) > 3:
                contact_sections.append(contact_text)

        contact_text = ' '.join(contact_sections) if contact_sections else text

        # Phone - More robust regex to capture common formats
        phone_patterns = [
            r'[\+]?[0-9]{1,3}[\s\-]?\(?[0-9]{1,4}\)?[\s\- ]?[0-9]{1,4}[\s\- ]?[0-9]{1,9}', # International format, Pakistan format
            r'[0-9]{10,11}', # Simple 10-11 digit number
            r'0[0-9]{10}', # Pakistani mobile format
            r'\+\(?[0-9]{1,3}\)?\s?(\d[\s-]?){6,}', # General international format
            r'tel:[\+\d\s\-]+', # tel: links
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, contact_text)
            if phone_match:
                phone = phone_match.group().strip()
                # Clean up tel: prefix
                phone = re.sub(r'^tel:', '', phone)
                contact["phone"] = phone
                break # Use the first one found

        # Also check for tel: links directly
        if not contact["phone"]:
            tel_link = soup.find('a', href=re.compile(r'^tel:', re.I))
            if tel_link:
                contact["phone"] = tel_link.get('href', '').replace('tel:', '').strip()

        # Email - search in contact sections first, then full text
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contact_text)
        if not email_match:
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            contact["email"] = email_match.group()

        # Also check for mailto: links
        if not contact["email"]:
            mailto_link = soup.find('a', href=re.compile(r'^mailto:', re.I))
            if mailto_link:
                contact["email"] = mailto_link.get('href', '').replace('mailto:', '').strip()

        # Address - Look for contact sections first with expanded keywords
        address_found = False
        address_keywords = ['street', 'road', 'avenue', 'lane', 'area', 'city', 'pakistan', 'pk', 'address', 'location',
                           'boulevard', 'drive', 'court', 'place', 'suite', 'floor', 'building', 'plaza', 'center',
                           'centre', 'block', 'phase', 'sector', 'town', 'country', 'zip', 'postal']

        for section in contact_sections:
            address_lines = [line.strip() for line in section.split('\n')
                           if len(line.strip().split()) > 3
                           and any(kw in line.lower() for kw in address_keywords)]
            if address_lines:
                contact["address"] = ", ".join(address_lines[:2])
                address_found = True
                break

        if not address_found:
            address_lines = [line.strip() for line in text.split('\n')
                           if len(line.strip().split()) > 3
                           and any(kw in line.lower() for kw in address_keywords)]
            if address_lines:
                contact["address"] = ", ".join(address_lines[:2])

        # Business hours - look for timing patterns with expanded search
        hours_patterns = [
            r'(?i)(?:opening\s*(?:hours|times?)|business\s*hours?|working\s*hours?|hours[:\s]+)\s*[:\-]?\s*([a-z0-9\s,\-\:]+(?:am|pm|mon|tue|wed|thu|fri|sat|sun)+)',
            r'(?i)(?:mon|tue|wed|thu|fri|sat|sun)[a-z\s]*[\d\s\-:am]+',
            r'(?i)(?:9|10|8)\s*am?\s*[-–to]+\s*(?:5|6|pm)',  # e.g., "9am - 5pm"
        ]
        for pattern in hours_patterns:
            hours_match = re.search(pattern, contact_text, re.IGNORECASE)
            if hours_match:
                contact["hours"] = hours_match.group(0).strip()[:100]
                break

        # Also look for hours in dedicated elements
        if not contact["hours"]:
            for tag in soup.find_all(['div', 'span', 'p'], class_=re.compile(r'hours|time|schedule', re.I)):
                hours_text = tag.get_text(strip=True)
                if re.search(r'(am|pm|mon|tue|wed|thu|fri|sat|sun)', hours_text, re.I):
                    contact["hours"] = hours_text[:100]
                    break

        logger.info(f"Extracted contact: {contact}")
        return contact

    @staticmethod
    def _extract_about_info(html: str, soup: BeautifulSoup) -> str:
        # Simple extraction for prompt context
        for s in soup(['script', 'style', 'nav', 'footer']): s.decompose()
        about_text = soup.get_text(separator=' ', strip=True)[:1000]
        logger.info(f"Extracted about text (truncated): {about_text[:50]}...")
        return about_text

    @staticmethod
    def _extract_services(html: str, soup: BeautifulSoup) -> list:
        services = []
        # Expanded keywords for service detection
        keywords = [
            'service', 'solution', 'offer', 'provide', 'expert', 'feature',
            'specialize', 'package', 'plan', 'product', 'category', 'section',
            'department', 'program', 'support', 'help', 'guide', 'tutorial',
            'resource', 'tool', 'platform', 'system', 'software', 'app'
        ]

        # Also look for navigation items and menu links
        nav_items = []
        for nav in soup.find_all(['nav', 'ul'], class_=re.compile(r'menu|nav|menu-item', re.I)):
            for li in nav.find_all('li'):
                nav_items.append(li.get_text(strip=True))

        # Search in headings and links
        for h in soup.find_all(['h2', 'h3', 'h4', 'h5', 'li', 'a']):
            t = h.get_text(strip=True)
            # Clean up whitespace and normalize
            t = ' '.join(t.split())
            if 5 < len(t) < 100:
                # Check for keyword match
                if any(k in t.lower() for k in keywords):
                    # Filter out generic text
                    if not any(generic in t.lower() for generic in ['click here', 'read more', 'learn more', 'view all']):
                        if t not in services:
                            services.append(t)
                            logger.debug(f"Potential service found: {t}")

        # Also extract from nav items (often contain service names)
        for item in nav_items:
            item = ' '.join(item.split())
            if 5 < len(item) < 80 and item not in services:
                if not any(generic in item.lower() for generic in ['home', 'contact', 'about', 'login', 'sign']):
                    services.append(item)
                    logger.debug(f"Potential service from nav: {item}")

        if not services:
            logger.warning("No services found using keywords. Trying generic headings.")
            # Fallback: look for any short, non-generic headings if no keywords matched
            for h in soup.find_all(['h2', 'h3', 'h4', 'h5']):
                 t = h.get_text(strip=True)
                 t = ' '.join(t.split())  # Normalize whitespace
                 if 5 < len(t) < 100 and 2 <= len(t.split()) <= 6:  # Reasonable heading length
                     # Filter generic headings
                     if not any(generic in t.lower() for generic in ['welcome', 'latest', 'featured', 'popular']):
                         if t not in services:
                            services.append(t)
                            logger.debug(f"Potential service found (fallback): {t}")

        final_services = services[:15] # Limit to 15 services
        logger.info(f"Extracted {len(final_services)} services.")
        return final_services

    @staticmethod
    def scrape_products_from_website(base_url: str, limit: int = 50) -> dict:
        result = {"success": False, "products": [], "categories": [], "total_products": 0}
        try:
            logger.info(f"🔍 Scraping products from: {base_url} (limit: {limit})")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            # Try home page first
            urls_to_try = [base_url.rstrip("/")]
            # Also try /shop and /products if they exist
            for path in ["/shop", "/products", "/collections/all"]:
                urls_to_try.append(base_url.rstrip("/") + path)

            extracted_products = []
            seen_names = set()

            for url in urls_to_try:
                if len(extracted_products) >= limit: break
                try:
                    logger.debug(f"Scraping URL: {url}")
                    resp = requests.get(url, timeout=12, verify=False, headers=headers)
                    if resp.status_code != 200:
                        continue
                    
                    html = resp.text
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 1. Try Schema.org Product markup
                    schema_products = soup.find_all(itemtype=re.compile(r'Product', re.I))
                    for item in schema_products:
                        if len(extracted_products) >= limit: break
                        name_elem = item.find(itemprop="name")
                        price_elem = item.find(itemprop="price") or item.find(class_=re.compile(r'price', re.I))
                        
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            if name and name not in seen_names:
                                price = price_elem.get_text(strip=True) if price_elem else "Contact us"
                                extracted_products.append({"name": name, "price": price})
                                seen_names.add(name)

                    # 2. Broadly look for product-like containers
                    patterns = [
                        re.compile(r'product', re.I), re.compile(r'item', re.I), 
                        re.compile(r'card', re.I), re.compile(r'entry', re.I),
                        re.compile(r'shop', re.I), re.compile(r'grid', re.I),
                        re.compile(r'listing', re.I), re.compile(r'detail', re.I)
                    ]
                    
                    found_items = []
                    for pattern in patterns:
                        found_items.extend(soup.find_all(class_=pattern))
                        found_items.extend(soup.find_all(id=pattern))
                    
                    for item in found_items:
                        if len(extracted_products) >= limit: break
                        if len(item.get_text()) < 10 or item.name in ['body', 'html']:
                            continue

                        name_tag = item.find(['h1', 'h2', 'h3', 'h4', 'a', 'strong', 'span'], class_=re.compile(r'(name|title|heading|caption)', re.I))
                        if not name_tag and item.name in ['h2', 'h3', 'h4']:
                            name_tag = item
                        
                        if name_tag:
                            name = name_tag.get_text(strip=True)
                            if name and 3 < len(name) < 150 and not name.isnumeric() and len(re.findall(r'[a-zA-Z]', name)) > 1:
                                if name not in seen_names:
                                    price = "Contact us"
                                    price_patterns = [r'price', r'amount', r'cost', r'value', r'sale']
                                    price_tag = item.find(['span', 'div', 'p', 'b'], class_=re.compile('|'.join(price_patterns), re.I))
                                    
                                    if price_tag:
                                        price_text = price_tag.get_text(strip=True)
                                        price_match = re.search(r'([R|r][s|S]?\.?\s?\d+[\d,.]*|[P|p][K|K][R|R]\s?\d+[\d,.]*|\$\s?\d+[\d,.]*|€\s?\d+[\d,.]*|£\s?\d+[\d,.]*)', price_text)
                                        if price_match:
                                            price = price_match.group()
                                    
                                    if price == "Contact us":
                                        all_text = item.get_text(separator=' ', strip=True)
                                        price_match = re.search(r'([R|r][s|S]?\.?\s?\d+[\d,.]*|[P|p][K|K][R|R]\s?\d+[\d,.]*|\$\s?\d+[\d,.]*|€\s?\d+[\d,.]*|£\s?\d+[\d,.]*)', all_text)
                                        if price_match:
                                            price = price_match.group()

                                    extracted_products.append({"name": name, "price": price})
                                    seen_names.add(name)
                except Exception as e:
                    logger.debug(f"Error scraping {url}: {e}")

            if extracted_products:
                result["success"] = True
                result["products"] = extracted_products
                result["total_products"] = len(extracted_products)
                logger.info(f"✅ Successfully scraped {result['total_products']} items from website")
            else:
                logger.warning(f"Could not scrape any products from {base_url}")
        except Exception as e:
            logger.error(f"Scraping {base_url} failed: {e}")
        return result

    @staticmethod
    def fetch_products_with_auth(base_url: str, key: str, secret: str) -> dict:
        res = {"success": False, "products": [], "categories": [], "method": "api"}
        try:
            logger.info(f"Attempting to fetch products via WooCommerce API for: {base_url}")
            url = f"{base_url.rstrip('/')}/wc/v3/products"
            headers = {"User-Agent": "Mozilla/5.0"} # Add user-agent for API calls too
            r = requests.get(url, params={"consumer_key": key, "consumer_secret": secret, "per_page": 50}, timeout=20, verify=False, headers=headers)
            logger.info(f"WooCommerce API request to {url}: Status code {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list): # Ensure response is a list of products
                    res["products"] = [{"name": p.get('name', 'Unnamed Product'), "price": p.get('price', 'Contact us')} for p in data]
                    res["success"] = True
                    res["total_products"] = len(res["products"])
                    logger.info(f"Successfully fetched {res['total_products']} products via WooCommerce API.")
                else:
                    logger.warning(f"WooCommerce API returned unexpected data format: {data}")
            else:
                logger.warning(f"WooCommerce API request failed for {base_url} with status code: {r.status_code}. Response: {r.text}")
                # Fallback to scraping if API fails
                logger.info(f"Falling back to scraping products from {base_url}")
                return UniversalWebsiteFetcher.scrape_products_from_website(base_url)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WooCommerce API request failed for {base_url}: {e}")
            logger.info(f"Falling back to scraping products from {base_url}")
            return UniversalWebsiteFetcher.scrape_products_from_website(base_url)
        except Exception as e:
            logger.error(f"An unexpected error occurred during WooCommerce API fetch for {base_url}: {e}")
            logger.info(f"Falling back to scraping products from {base_url}")
            return UniversalWebsiteFetcher.scrape_products_from_website(base_url)
        return res

    @staticmethod
    def fetch_wordpress_pages(base_url: str) -> dict:
        res = {"success": False, "pages": {}, "contact_info": {}}
        try:
            logger.info(f"Attempting to fetch WordPress pages from: {base_url}")
            url = f"{base_url.rstrip('/')}/wp-json/wp/v2/pages"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, params={"per_page": 10}, timeout=15, verify=False, headers=headers)
            logger.info(f"WordPress API request to {url}: Status code {r.status_code}")

            if r.status_code == 200:
                pages = r.json()
                if isinstance(pages, list): # Ensure response is a list of pages
                    for p in pages:
                        slug = p.get('slug')
                        content = p.get('content', {}).get('rendered', '')
                        # Basic sanitization to remove HTML tags, limit length
                        sanitized_content = re.sub(r'<[^>]+>', '', content)[:1000] if content else ""
                        if slug and sanitized_content:
                            res["pages"][slug] = {"content": sanitized_content}
                    res["success"] = True
                    logger.info(f"Successfully fetched {len(res['pages'])} WordPress pages.")
                else:
                    logger.warning(f"WordPress API returned unexpected data format: {pages}")
            else:
                logger.warning(f"WordPress API request failed for {base_url} with status code: {r.status_code}. Response: {r.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"WordPress API request failed for {base_url}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during WordPress API fetch for {base_url}: {e}")
        return res

    @staticmethod
    def auto_discover_and_fetch(website_url: str, integration_id: Optional[int] = None) -> dict:
        """
        Automatically detect platform and fetch all available data (info, products, pages).
        Consolidates results for easier integration setup.
        If integration_id is provided, saves results to the database.
        """
        website_url = UniversalWebsiteFetcher.normalize_url(website_url)
        logger.info(f"🚀 Starting auto-discovery for: {website_url}")
        
        result = {
            "success": False,
            "platform": "unknown",
            "site_info": {},
            "products": [],
            "pages": {},
            "total_products": 0,
            "message": ""
        }
        
        try:
            # 1. Detect platform
            plat_info = UniversalWebsiteFetcher.detect_platform(website_url)
            result["platform"] = plat_info["platform"]
            
            # 2. Fetch basic site info
            result["site_info"] = UniversalWebsiteFetcher.fetch_site_info(website_url)
            
            # 3. Fetch products (scrape by default for discovery)
            prod_res = UniversalWebsiteFetcher.scrape_products_from_website(website_url)
            if prod_res["success"]:
                result["products"] = prod_res["products"]
                result["total_products"] = prod_res["total_products"]
            
            # 4. If WordPress/WooCommerce, fetch pages
            if plat_info["is_wordpress"] or plat_info["is_woocommerce"]:
                pages_res = UniversalWebsiteFetcher.fetch_wordpress_pages(website_url)
                if pages_res["success"]:
                    result["pages"] = pages_res["pages"]
            
            result["success"] = True
            result["message"] = f"Successfully discovered {result['platform']} site with {result['total_products']} products."
            logger.info(f"✅ Auto-discovery completed for {website_url}. Platform: {result['platform']}, Products: {result['total_products']}")

            # 5. Save to database if integration_id is provided
            if integration_id:
                try:
                    from database import SessionLocal
                    from models import Integration
                    import json
                    
                    db = SessionLocal()
                    try:
                        integ = db.query(Integration).filter(Integration.id == integration_id).first()
                        if integ:
                            integ.woo_products_cached = True
                            integ.woo_products_count = result["total_products"]
                            # If no categories found during scraping, just store empty list
                            integ.woo_categories_cached = json.dumps([])
                            
                            # Update URLs if they were missing
                            if result["platform"] == "woocommerce" and not integ.woocommerce_url:
                                integ.woocommerce_url = website_url
                            if (result["platform"] == "wordpress" or result["platform"] == "woocommerce") and not integ.wp_base_url:
                                integ.wp_base_url = website_url
                                
                            db.commit()
                            logger.info(f"💾 Saved discovery results to integration ID: {integration_id}")
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"Failed to save discovery results to DB: {db_err}")
            
        except Exception as e:
            logger.error(f"❌ Auto-discovery failed for {website_url}: {e}")
            result["message"] = f"Discovery failed: {str(e)}"
            
        return result
