"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path

app = FastAPI(title="Slalom Capabilities Management API",
              description="API for managing consulting capabilities and consultant expertise")

audit_log = logging.getLogger("audit")
if not audit_log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s AUDIT %(message)s"))
    audit_log.addHandler(_handler)
    audit_log.setLevel(logging.INFO)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory capabilities database
capabilities = {
    "Cloud Architecture": {
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,  # hours per week available across team
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"]
    },
    "Data Analytics": {
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology", 
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"]
    },
    "DevOps Engineering": {
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"], 
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"]
    },
    "Digital Strategy": {
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"]
    },
    "Change Management": {
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"]
    },
    "UX/UI Design": {
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"]
    },
    "Cybersecurity": {
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"]
    },
    "Business Intelligence": {
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"]
    },
    "Agile Coaching": {
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"]
    }
}


# Practice lead accounts live in a JSON file until a database exists
SESSION_TTL_SECONDS = 8 * 60 * 60
sessions = {}  # token -> {"username": str, "expires": float}


def load_practice_leads():
    with open(current_dir / "practice_leads.json", encoding="utf-8") as f:
        return {lead["username"]: lead for lead in json.load(f)["practice_leads"]}


practice_leads = load_practice_leads()


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        _, iterations, salt_hex, hash_hex = stored_hash.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


# Used to keep login timing the same for unknown usernames
DUMMY_HASH = "pbkdf2_sha256$600000$" + "00" * 16 + "$" + "00" * 32


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_lead(authorization: str | None = Header(default=None)):
    """Resolve the practice lead for a Bearer session token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[len("Bearer "):]
    session = sessions.get(token)
    if not session or session["expires"] < time.time():
        sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return {**practice_leads[session["username"]], "token": token}


def require_practice_area(lead: dict, capability: dict):
    if capability["practice_area"] not in lead["practice_areas"]:
        raise HTTPException(
            status_code=403,
            detail=f"You are not authorized to manage {capability['practice_area']} capabilities"
        )


def public_profile(lead: dict):
    return {"username": lead["username"], "name": lead["name"],
            "role": lead["role"], "practice_areas": lead["practice_areas"]}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def login(credentials: LoginRequest):
    """Authenticate a practice lead and start a session"""
    lead = practice_leads.get(credentials.username)
    valid = verify_password(
        credentials.password, lead["password_hash"] if lead else DUMMY_HASH)
    if not lead or not valid:
        audit_log.warning("login_failed username=%r", credentials.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    sessions[token] = {"username": lead["username"],
                       "expires": time.time() + SESSION_TTL_SECONDS}
    audit_log.info("login username=%s", lead["username"])
    return {"token": token, "user": public_profile(lead)}


@app.post("/auth/logout")
def logout(lead: dict = Depends(get_current_lead)):
    sessions.pop(lead["token"], None)
    audit_log.info("logout username=%s", lead["username"])
    return {"message": "Logged out"}


@app.get("/auth/me")
def me(lead: dict = Depends(get_current_lead)):
    return public_profile(lead)


@app.get("/capabilities")
def get_capabilities(practice_area: str | None = None,
                     industry_vertical: str | None = None):
    """List capabilities, optionally filtered by practice area and/or industry vertical"""
    result = capabilities
    if practice_area:
        result = {name: c for name, c in result.items()
                  if c["practice_area"].lower() == practice_area.lower()}
    if industry_vertical:
        result = {name: c for name, c in result.items()
                  if industry_vertical.lower() in
                  (v.lower() for v in c["industry_verticals"])}
    return result


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, email: str,
                            lead: dict = Depends(get_current_lead)):
    """Register a consultant for a capability (practice leads only)"""
    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Get the specific capability
    capability = capabilities[capability_name]
    require_practice_area(lead, capability)

    # Validate consultant is not already registered
    if email in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is already registered for this capability"
        )

    # Add consultant
    capability["consultants"].append(email)
    audit_log.info("register actor=%s capability=%r consultant=%s",
                   lead["username"], capability_name, email)
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(capability_name: str, email: str,
                               lead: dict = Depends(get_current_lead)):
    """Unregister a consultant from a capability (practice leads only)"""
    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Get the specific capability
    capability = capabilities[capability_name]
    require_practice_area(lead, capability)

    # Validate consultant is registered
    if email not in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is not registered for this capability"
        )

    # Remove consultant
    capability["consultants"].remove(email)
    audit_log.info("unregister actor=%s capability=%r consultant=%s",
                   lead["username"], capability_name, email)
    return {"message": f"Unregistered {email} from {capability_name}"}
