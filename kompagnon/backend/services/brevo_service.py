import os

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


class BrevoService:
    def __init__(self):
        api_key = os.environ.get("BREVO_API_KEY")
        if not api_key:
            raise RuntimeError("BREVO_API_KEY ist nicht gesetzt")

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key
        self._api_client = sib_api_v3_sdk.ApiClient(configuration)

    def create_contact(self, email, first_name, last_name, list_ids):
        """Erstellt einen Kontakt in Brevo und gibt die ID zurueck."""
        try:
            api = sib_api_v3_sdk.ContactsApi(self._api_client)
            contact = sib_api_v3_sdk.CreateContact(
                email=email,
                attributes={"FIRSTNAME": first_name, "LASTNAME": last_name},
                list_ids=list_ids,
            )
            response = api.create_contact(contact)
            return response.id
        except ApiException as e:
            return f"Fehler beim Erstellen des Kontakts: {e}"

    def create_email_campaign(self, title, subject, html_content, list_id, scheduled_at=None):
        """Erstellt eine E-Mail-Kampagne und gibt die brevo_campaign_id zurueck."""
        try:
            api = sib_api_v3_sdk.EmailCampaignsApi(self._api_client)
            campaign = sib_api_v3_sdk.CreateEmailCampaign(
                name=title,
                subject=subject,
                html_content=html_content,
                sender={"name": "Silva Viridis", "email": "newsletter@silva-viridis.de"},
                recipients={"listIds": [list_id]},
            )
            if scheduled_at:
                campaign.scheduled_at = scheduled_at
            response = api.create_email_campaign(campaign)
            return response.id
        except ApiException as e:
            return f"Fehler beim Erstellen der Kampagne: {e}"

    def get_campaign_stats(self, brevo_campaign_id):
        """Gibt Kampagnen-Statistiken zurueck (openRate, clickRate, unsubscriptions)."""
        try:
            api = sib_api_v3_sdk.EmailCampaignsApi(self._api_client)
            result = api.get_email_campaign(brevo_campaign_id)
            stats = result.statistics.global_stats
            return {
                "openRate": stats.open_rate if hasattr(stats, "open_rate") else None,
                "clickRate": stats.click_rate if hasattr(stats, "click_rate") else None,
                "unsubscriptions": stats.unsubscriptions if hasattr(stats, "unsubscriptions") else None,
                "sentCount": stats.sent if hasattr(stats, "sent") else None,
            }
        except ApiException as e:
            return f"Fehler beim Abrufen der Statistiken: {e}"

    def create_list(self, name, folder_id=1):
        """Erstellt eine neue Kontaktliste in Brevo und gibt die List-ID zurueck."""
        try:
            api = sib_api_v3_sdk.ContactsApi(self._api_client)
            create_list = sib_api_v3_sdk.CreateList(name=name, folder_id=folder_id)
            response = api.create_list(create_list)
            return response.id
        except ApiException as e:
            return f"Fehler beim Erstellen der Liste: {e}"

    def send_campaign_now(self, brevo_campaign_id):
        """Sendet eine Kampagne sofort."""
        try:
            api = sib_api_v3_sdk.EmailCampaignsApi(self._api_client)
            api.send_email_campaign_now(brevo_campaign_id)
            return True
        except ApiException as e:
            return f"Fehler beim Senden der Kampagne: {e}"
