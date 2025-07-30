from database.db import SessionLocal
from database.models import Lead, Campaign
from sqlalchemy.orm import Session
from typing import List
import uuid


def save_leads_to_db(user_id: int, campaign_name: str, leads: List[dict]):
    session: Session = SessionLocal()

    # Get campaign id
    campaign = session.query(Campaign).filter_by(user_id=user_id, name=campaign_name).first()
    if not campaign:
        raise Exception("Campaign not found in DB")

    # Delete old leads for this campaign
    deleted_leads = session.query(Lead).filter_by(campaign_id=campaign.id).delete()
    # Delete old EmailContent for this campaign
    from database.models import EmailContent
    deleted_emails = session.query(EmailContent).filter_by(campaign_id=campaign.id).delete()
    session.commit()
    print(f"🗑️ Deleted {deleted_leads} old leads and {deleted_emails} old emails for campaign '{campaign_name}'.")

    # Deduplicate leads by email and name (case-insensitive)
    unique = {}
    for lead in leads:
        email = (lead.get("email") or '').strip().lower()
        name = (lead.get("name") or '').strip().lower()
        key = f"{email}|{name}"
        if email and name and key not in unique:
            unique[key] = lead

    # Add new leads
    for lead in unique.values():
        lead_entry = Lead(
            campaign_id=campaign.id,
            name=lead.get("name"),
            email=lead.get("email"),
            platform_source=lead.get("platform_source"),
            profile_link=lead.get("profile_link"),
            website=lead.get("website"),
            state=lead.get("state"),
            industry=lead.get("industry"),
            profile_description=lead.get("profile_description"),
            delivery_status="Pending"
        )
        session.add(lead_entry)

    session.commit()
    print(f"✅ Saved {len(unique)} new unique leads to database for campaign '{campaign_name}'.")
    session.close()
