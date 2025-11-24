"""Advanced email validation utilities."""
import re
from typing import Tuple
from email_validator import validate_email, EmailNotValidError
import dns.resolver

def validate_email_address(email: str, check_deliverability: bool = True) -> Tuple[bool, str, str]:
    """
    Validate email address with multiple checks.
    
    Returns:
        (is_valid, normalized_email, error_message)
    """
    if not email:
        return False, "", "Empty email"
    
    # Clean email
    email = email.strip().lower()
    
    # Basic regex check first (fast pre-filter)
    basic_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(basic_pattern, email):
        return False, email, "Invalid format"
    
    # Use email-validator library for comprehensive validation
    try:
        validation = validate_email(email, check_deliverability=check_deliverability)
        normalized = validation.normalized
        return True, normalized, ""
    except EmailNotValidError as e:
        return False, email, str(e)

def check_mx_records(domain: str) -> bool:
    """Check if domain has valid MX records."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return len(mx_records) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return False
    except Exception:
        return False

def extract_emails_from_text(text: str) -> list[str]:
    """Extract potential email addresses from text using regex."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return list(set(emails))  # Remove duplicates