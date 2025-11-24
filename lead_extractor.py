"""Main lead extraction pipeline using Firecrawl v2."""
import json
import csv
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from tqdm import tqdm

from firecrawl import Firecrawl
from config import Config
from email_validator_utils import validate_email_address, extract_emails_from_text

@dataclass
class Lead:
    """Lead data structure."""
    url: str
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source_page: Optional[str] = None
    confidence: float = 0.0

class LeadExtractor:
    """Lead extraction orchestrator."""
    
    def __init__(self, api_key: str):
        """Initialize with Firecrawl client."""
        self.client = Firecrawl(api_key=api_key)
        self.leads: List[Lead] = []
        
    def filter_candidate_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs likely to contain contact information."""
        keywords = [
            'about', 'team', 'contact', 'people', 'leadership', 
            'founder', 'staff', 'employee', 'management', 'executive',
            'our-team', 'meet-', 'who-we-are', 'board', 'directors'
        ]
        
        candidates = []
        for url in urls:
            url_lower = url.lower()
            
            # Check if URL contains any keyword
            if any(keyword in url_lower for keyword in keywords):
                candidates.append(url)
                continue
            
            # Check if URL ends with specific paths
            if url_lower.endswith('/about') or url_lower.endswith('/contact') or url_lower.endswith('/team'):
                candidates.append(url)
        
        # If no candidates found, return first N URLs
        if not candidates:
            print("⚠️  No candidate pages found, using first 50 URLs as fallback")
            return urls[:50]
        
        return candidates
    
    def crawl_site(self, domain: str, max_pages: int = 100) -> List[str]:
        """
        Crawl site and discover URLs.
        Uses Firecrawl v2 crawl endpoint.
        """
        print(f"🔍 Crawling {domain}...")
        
        try:
            # Start crawl job
            crawl_result = self.client.crawl(
                url=domain,
                limit=max_pages,
                scrape_options={
                    'formats': ['markdown']
                }
            )
            
            # Extract URLs from crawl results
            urls = []
            if hasattr(crawl_result, 'data') and crawl_result.data:
                for item in crawl_result.data:
                    if hasattr(item, 'url'):
                        urls.append(item.url)
                    elif isinstance(item, dict) and 'url' in item:
                        urls.append(item['url'])
            
            print(f"✅ Found {len(urls)} pages")
            return urls
            
        except Exception as e:
            print(f"❌ Crawl failed: {e}")
            # Fallback: try map endpoint
            return self.map_site(domain)
    
    def map_site(self, domain: str) -> List[str]:
        """
        Map site URLs without scraping (faster).
        Uses Firecrawl v2 map endpoint.
        """
        print(f"🗺️  Mapping {domain}...")
        
        try:
            map_result = self.client.map(url=domain)
            
            urls = []
            if hasattr(map_result, 'links'):
                urls = map_result.links
            elif isinstance(map_result, dict) and 'links' in map_result:
                urls = map_result['links']
            
            print(f"✅ Mapped {len(urls)} URLs")
            return urls
            
        except Exception as e:
            print(f"❌ Map failed: {e}")
            return []
    
    def extract_from_pages(self, urls: List[str], use_batch: bool = True) -> List[Dict[str, Any]]:
        """
        Extract structured lead data from pages.
        Uses batch scraping for efficiency.
        """
        print(f"📊 Extracting data from {len(urls)} pages...")
        
        # Define extraction schema
        extraction_schema = {
            'type': 'object',
            'properties': {
                'contacts': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Full name of person'},
                            'title': {'type': 'string', 'description': 'Job title or role'},
                            'email': {'type': 'string', 'description': 'Email address'},
                            'linkedin': {'type': 'string', 'description': 'LinkedIn profile URL'},
                            'phone': {'type': 'string', 'description': 'Phone number'},
                            'company': {'type': 'string', 'description': 'Company name'}
                        }
                    }
                }
            }
        }
        
        all_results = []
        
        if use_batch and len(urls) > 1:
            # Batch scrape with structured extraction
            batch_size = Config.BATCH_SIZE
            
            for i in tqdm(range(0, len(urls), batch_size), desc="Batch scraping"):
                batch_urls = urls[i:i + batch_size]
                
                try:
                    # Use batch scrape with JSON format extraction
                    batch_result = self.client.batch_scrape(
                        urls=batch_urls,
                        formats=[
                            'markdown',
                            {
                                'type': 'json',
                                'schema': extraction_schema
                            }
                        ],
                        poll_interval=3
                    )
                    
                    # Process results
                    if hasattr(batch_result, 'data'):
                        for item in batch_result.data:
                            result = self._process_scraped_item(item)
                            all_results.extend(result)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"⚠️  Batch {i//batch_size + 1} failed: {e}")
                    # Fallback to individual scraping
                    for url in batch_urls:
                        try:
                            result = self._scrape_single_url(url, extraction_schema)
                            all_results.extend(result)
                            time.sleep(0.2)
                        except Exception as e2:
                            print(f"⚠️  Failed {url}: {e2}")
        else:
            # Individual scraping
            for url in tqdm(urls, desc="Scraping"):
                try:
                    result = self._scrape_single_url(url, extraction_schema)
                    all_results.extend(result)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"⚠️  Failed {url}: {e}")
        
        return all_results
    
    def _scrape_single_url(self, url: str, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape single URL with structured extraction."""
        scrape_result = self.client.scrape(
            url=url,
            formats=[
                'markdown',
                {
                    'type': 'json',
                    'schema': schema
                }
            ]
        )
        return self._process_scraped_item(scrape_result)
    
    def _process_scraped_item(self, item: Any) -> List[Dict[str, Any]]:
        """Process a scraped item and extract leads."""
        results = []
        
        # Get URL
        url = getattr(item, 'url', None) or (item.get('url') if isinstance(item, dict) else None)
        
        # Get markdown content for fallback email extraction
        markdown = getattr(item, 'markdown', None) or (item.get('markdown') if isinstance(item, dict) else '')
        
        # Get JSON data
        json_data = None
        if hasattr(item, 'json'):
            json_data = item.json
        elif isinstance(item, dict) and 'json' in item:
            json_data = item['json']
        
        # Extract from structured data
        if json_data and isinstance(json_data, dict):
            contacts = json_data.get('contacts', [])
            for contact in contacts:
                if isinstance(contact, dict):
                    results.append({
                        'url': url,
                        'name': contact.get('name'),
                        'title': contact.get('title'),
                        'email': contact.get('email'),
                        'linkedin': contact.get('linkedin'),
                        'phone': contact.get('phone'),
                        'company': contact.get('company')
                    })
        
        # Fallback: extract emails from markdown
        if markdown:
            emails = extract_emails_from_from_text(markdown)
            for email in emails:
                results.append({
                    'url': url,
                    'email': email
                })
        
        return results
    
    def validate_and_deduplicate(self, raw_results: List[Dict[str, Any]]) -> List[Lead]:
        """Validate emails and remove duplicates."""
        print("✅ Validating and deduplicating leads...")
        
        seen_emails = set()
        valid_leads = []
        
        for result in tqdm(raw_results, desc="Validating"):
            email = result.get('email')
            
            # Skip if no email
            if not email:
                continue
            
            # Validate email
            is_valid, normalized_email, error = validate_email_address(
                email, 
                check_deliverability=Config.CHECK_DELIVERABILITY
            )
            
            if not is_valid:
                continue
            
            # Skip duplicates
            if normalized_email in seen_emails:
                continue
            
            seen_emails.add(normalized_email)
            
            # Create lead
            lead = Lead(
                url=result.get('url', ''),
                name=result.get('name'),
                title=result.get('title'),
                email=normalized_email,
                linkedin=result.get('linkedin'),
                company=result.get('company'),
                phone=result.get('phone')
            )
            
            valid_leads.append(lead)
        
        return valid_leads
    
    def save_results(self, leads: List[Lead], base_filename: str = "leads"):
        """Save leads to multiple formats."""
        output_dir = Config.OUTPUT_DIR
        
        # Save as JSON
        json_file = output_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(lead) for lead in leads], f, indent=2, ensure_ascii=False)
        print(f"💾 Saved JSON: {json_file}")
        
        # Save as CSV
        csv_file = output_dir / f"{base_filename}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if leads:
                fieldnames = asdict(leads[0]).keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lead in leads:
                    writer.writerow(asdict(lead))
        print(f"💾 Saved CSV: {csv_file}")
        
        # Save emails to TXT (one per line)
        txt_file = output_dir / f"{base_filename}_emails.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for lead in leads:
                if lead.email:
                    f.write(f"{lead.email}
")
        print(f"💾 Saved TXT: {txt_file}")
        
        # Save emails to CSV (simple format)
        emails_csv_file = output_dir / f"{base_filename}_emails.csv"
        with open(emails_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email'])
            for lead in leads:
                if lead.email:
                    writer.writerow([lead.email])
        print(f"💾 Saved emails CSV: {emails_csv_file}")
        
        return {
            'json': json_file,
            'csv': csv_file,
            'txt': txt_file,
            'emails_csv': emails_csv_file
        }
    
    def run(self, domain: str, max_pages: int = None) -> Dict[str, Path]:
        """Run complete extraction pipeline."""
        max_pages = max_pages or Config.MAX_PAGES
        
        print(f"
🚀 Starting lead extraction for: {domain}
")
        
        # Step 1: Discover URLs
        urls = self.crawl_site(domain, max_pages)
        if not urls:
            print("❌ No URLs found. Exiting.")
            return {}
        
        # Step 2: Filter candidate pages
        candidates = self.filter_candidate_urls(urls)
        print(f"📋 Selected {len(candidates)} candidate pages
")
        
        # Step 3: Extract data
        raw_results = self.extract_from_pages(candidates[:max_pages])
        print(f"📦 Extracted {len(raw_results)} raw results
")
        
        # Step 4: Validate and deduplicate
        self.leads = self.validate_and_deduplicate(raw_results)
        print(f"✨ Final lead count: {len(self.leads)}
")
        
        # Step 5: Save results
        if self.leads:
            files = self.save_results(self.leads)
            print(f"
✅ Extraction complete! Found {len(self.leads)} valid leads")
            return files
        else:
            print("
⚠️  No valid leads found")
            return {}