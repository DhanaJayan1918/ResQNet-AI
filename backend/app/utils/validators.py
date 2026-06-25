"""
ResQNet AI - Custom Validators
Reusable validation functions for request data.
"""

import re
from typing import Optional


PHONE_PATTERN = re.compile(r"^\+?[\d\s\-()]{7,20}$")
INCIDENT_ID_PATTERN = re.compile(r"^RESQ-\d{8}-\d{4}$")
RESOURCE_ID_PATTERN = re.compile(r"^RES-[A-Z]{4}-\d{4}$")


def validate_phone(phone: Optional[str]) -> bool:
    """Validate phone number format."""
    if phone is None:
        return True
    return bool(PHONE_PATTERN.match(phone))


def validate_incident_id(incident_id: str) -> bool:
    """Validate incident ID format (RESQ-YYYYMMDD-XXXX)."""
    return bool(INCIDENT_ID_PATTERN.match(incident_id))


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographic coordinates."""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def sanitize_text(text: str) -> str:
    """Basic text sanitization — strip excessive whitespace, normalize."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text[:5000]  # Cap at max length
