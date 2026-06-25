"""
ResQNet AI - ID Generator
Generates human-readable, unique IDs for incidents, resources, shelters, etc.
Format: RESQ-YYYYMMDD-XXXX (e.g., RESQ-20240615-0001)
"""

from datetime import datetime
import random
import string


def generate_incident_id() -> str:
    """Generate a unique incident ID: RESQ-YYYYMMDD-XXXX."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"RESQ-{date_str}-{suffix}"


def generate_resource_id(resource_type: str) -> str:
    """Generate a unique resource ID: RES-TYPE-XXXX."""
    type_code = resource_type.upper()[:4]
    suffix = "".join(random.choices(string.digits, k=4))
    return f"RES-{type_code}-{suffix}"


def generate_shelter_id() -> str:
    """Generate a unique shelter ID: SHL-XXXX."""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"SHL-{suffix}"


def generate_hospital_id() -> str:
    """Generate a unique hospital ID: HSP-XXXX."""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"HSP-{suffix}"


def generate_brief_id() -> str:
    """Generate a unique command brief ID: BRF-YYYYMMDD-XXXX."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"BRF-{date_str}-{suffix}"
