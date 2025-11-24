"""Configuration management for lead extraction."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings."""
    
    # Firecrawl API
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    
    # Output settings
    OUTPUT_DIR: Path = Path("output")
    
    # CRM Integration (optional)
    HUBSPOT_API_KEY: Optional[str] = os.getenv("HUBSPOT_API_KEY")
    INSTANTLY_API_KEY: Optional[str] = os.getenv("INSTANTLY_API_KEY")
    
    # Push toggles
    PUSH_TO_HUBSPOT: bool = os.getenv("PUSH_TO_HUBSPOT", "false").lower() == "true"
    PUSH_TO_INSTANTLY: bool = os.getenv("PUSH_TO_INSTANTLY", "false").lower() == "true"
    
    # Validation settings
    CHECK_DNS: bool = os.getenv("CHECK_DNS", "true").lower() == "true"
    CHECK_DELIVERABILITY: bool = os.getenv("CHECK_DELIVERABILITY", "false").lower() == "true"
    
    # Processing settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "50"))
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "500"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.FIRECRAWL_API_KEY:
            raise ValueError("FIRECRAWL_API_KEY is required")
        
        # Create output directory
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

# Validate on import
Config.validate()