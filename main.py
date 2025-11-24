"""Main CLI entry point."""
import argparse
from config import Config
from lead_extractor import LeadExtractor
from crm_integrations import push_to_hubspot, push_to_instantly

def main():
    parser = argparse.ArgumentParser(
        description="Extract leads from websites using Firecrawl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --domain https://example.com
  python main.py --domain https://example.com --max-pages 200 --output my_leads
  python main main.py --domain https://example.com --push-hubspot
        """
    )
    
    parser.add_argument(
        '--domain',
        required=True,
        help='Target domain to extract leads from (e.g., https://example.com)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=Config.MAX_PAGES,
        help=f'Maximum number of pages to process (default: {Config.MAX_PAGES})'
    )
    
    parser.add_argument(
        '--output',
        default='leads',
        help='Base filename for output files (default: leads)'
    )
    
    parser.add_argument(
        '--push-hubspot',
        action='store_true',
        help='Push results to HubSpot CRM'
    )
    
    parser.add_argument(
        '--push-instantly',
        action='store_true',
        help='Push results to Instantly'
    )
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = LeadExtractor(api_key=Config.FIRECRAWL_API_KEY)
    
    # Run extraction
    files = extractor.run(args.domain, args.max_pages)
    
    # Push to CRMs if requested
    if files and extractor.leads:
        if args.push_hubspot or Config.PUSH_TO_HUBSPOT:
            push_to_hubspot(extractor.leads)
        
        if args.push_instantly or Config.PUSH_TO_INSTANTLY:
            push_to_instantly(extractor.leads)
    
    print("
✨ Done!")

if __name__ == "__main__":
    main()