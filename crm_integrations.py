"""CRM integration utilities."""
import requests
from typing import List
from tqdm import tqdm
from config import Config
from lead_extractor import Lead

def push_to_hubspot(leads: List[Lead]) -> None:
    """Push leads to HubSpot CRM."""
    if not Config.HUBSPOT_API_KEY:
        print("⚠️  HubSpot API key not configured")
        return
    
    print(f"📤 Pushing {len(leads)} leads to HubSpot...")
    
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    for lead in tqdm(leads, desc="HubSpot"):
        if not lead.email:
            continue
        
        payload = {
            "properties": {
                "email": lead.email,
                "firstname": lead.name.split()[0] if lead.name else "",
                "lastname": " ".join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else "",
                "jobtitle": lead.title or "",
                "company": lead.company or "",
                "phone": lead.phone or "",
                "linkedin": lead.linkedin or ""
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            success_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed {lead.email}: {e}")
    
    print(f"✅ Successfully pushed {success_count}/{len(leads)} leads to HubSpot")

def push_to_instantly(leads: List[Lead]) -> None:
    """Push leads to Instantly."""
    if not Config.INSTANTLY_API_KEY:
        print("⚠️  Instantly API key not configured")
        return
    
    print(f"📤 Pushing {len(leads)} leads to Instantly...")
    
    # Note: Update endpoint based on actual Instantly API docs
    url = "https://api.instantly.ai/v1/contacts"
    headers = {
        "Authorization": f"Bearer {Config.INSTANTLY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    for lead in tqdm(leads, desc="Instantly"):
        if not lead.email:
            continue
        
        payload = {
            "email": lead.email,
            "first_name": lead.name.split()[0] if lead.name else "",
            "last_name": " ".join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else "",
            "company": lead.company,
            "title": lead.title,
            "phone": lead.phone,
            "custom_fields": {
                "linkedin": lead.linkedin,
                "source": "firecrawl-extractor"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            success_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed {lead.email}: {e}")
    
    print(f"✅ Successfully pushed {success_count}/{len(leads)} leads to Instantly")