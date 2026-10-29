"""Site-wide settings. Edit the values below (or set the matching environment variables)
and they appear automatically in the footer, Contact page and page titles."""
import os

def env(k, d=""):
    return os.getenv(k, d)

SITE = {
    "name": env("SITE_NAME", "Finance & Poverty Nexus"),
    "tagline": env("SITE_TAGLINE", "Financial inclusion intelligence for poverty reduction in Rwanda"),
    "org": env("ORG_NAME", "Your Organization Name"),        # <-- shown in the copyright line
    "email": env("CONTACT_EMAIL", "info@your-domain.org"),   # <-- contact details
    "phone": env("CONTACT_PHONE", "+250 000 000 000"),
    "address": env("CONTACT_ADDRESS", "KG 000 St, Kigali, Rwanda"),
    "hours": env("CONTACT_HOURS", "Mon–Fri, 08:00–17:00 (CAT)"),
    "social": {  # leave a value empty to hide that icon
        "X / Twitter": env("SOCIAL_X", "#"),
        "LinkedIn": env("SOCIAL_LINKEDIN", "#"),
        "Facebook": env("SOCIAL_FACEBOOK", "#"),
        "GitHub": env("SOCIAL_GITHUB", "#"),
    },
    "data_source": "NISR / hackathon dataset",
}
SECRET_KEY = env("SECRET_KEY", "change-me-in-production")
DATA_DIR = env("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"))
