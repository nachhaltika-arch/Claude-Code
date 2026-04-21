import os
import logging

logger = logging.getLogger(__name__)

_brevo_available = False

try:
    import brevo_python as brevo_sdk
    _brevo_available = True
    logger.info("Brevo SDK (brevo-python) geladen")
except ImportError:
    try:
        import sib_api_v3_sdk as brevo_sdk
        _brevo_available = True
        logger.info("Brevo SDK (sib-api-v3-sdk) geladen")
    except ImportError:
        logger.warning(
            "Brevo SDK nicht installiert — Newsletter-Funktionen deaktiviert. "
            "Installieren mit: pip install brevo-python"
        )
        brevo_sdk = None


class BrevoService:
    def __init__(self):
        if not _brevo_available:
            raise RuntimeError(
                "Brevo SDK nicht installiert. "
                "Bitte 'brevo-python' in requirements.txt eintragen."
            )

        api_key = os.environ.get("BREVO_API_KEY")
        if not api_key:
            raise RuntimeError("BREVO_API_KEY ist nicht gesetzt")

        configuration = brevo_sdk.Configuration()
        configuration.api_key["api-key"] = api_key
        self._api_client = brevo_sdk.ApiClient(configuration)

    def create_contact(self, email, first_name, last_name, list_ids):
        try:
            api = brevo_sdk.ContactsApi(self._api_client)
            contact = brevo_sdk.CreateContact(
                email=email,
                attributes={"FIRSTNAME": first_name, "LASTNAME": last_name},
                list_ids=list_ids,
            )
            response = api.create_contact(contact)
            return response.id
        except Exception as e:
            logger.error(f"Brevo create_contact Fehler: {e}")
            return f"Fehler beim Erstellen des Kontakts: {e}"

    def create_email_campaign(self, title, subject, html_content, list_id, scheduled_at=None):
        try:
            api = brevo_sdk.EmailCampaignsApi(self._api_client)
            campaign = brevo_sdk.CreateEmailCampaign(
                name=title,
                subject=subject,
                html_content=html_content,
                sender={"name": "KOMPAGNON", "email": "info@kompagnon.eu"},
                recipients={"listIds": [list_id]},
            )
            if scheduled_at:
                campaign.scheduled_at = scheduled_at
            response = api.create_email_campaign(campaign)
            return response.id
        except Exception as e:
            logger.error(f"Brevo create_email_campaign Fehler: {e}")
            return f"Fehler beim Erstellen der Kampagne: {e}"

    def get_campaign_stats(self, brevo_campaign_id):
        try:
            api = brevo_sdk.EmailCampaignsApi(self._api_client)
            result = api.get_email_campaign(brevo_campaign_id)
            stats = result.statistics.global_stats
            return {
                "openRate": getattr(stats, "open_rate", None),
                "clickRate": getattr(stats, "click_rate", None),
                "unsubscriptions": getattr(stats, "unsubscriptions", None),
                "sentCount": getattr(stats, "sent", None),
            }
        except Exception as e:
            logger.error(f"Brevo get_campaign_stats Fehler: {e}")
            return f"Fehler beim Abrufen der Statistiken: {e}"

    def create_list(self, name, folder_id=1):
        try:
            api = brevo_sdk.ContactsApi(self._api_client)
            create_list = brevo_sdk.CreateList(name=name, folder_id=folder_id)
            response = api.create_list(create_list)
            return response.id
        except Exception as e:
            logger.error(f"Brevo create_list Fehler: {e}")
            return f"Fehler beim Erstellen der Liste: {e}"

    def send_campaign_now(self, brevo_campaign_id):
        try:
            api = brevo_sdk.EmailCampaignsApi(self._api_client)
            api.send_email_campaign_now(brevo_campaign_id)
            return True
        except Exception as e:
            logger.error(f"Brevo send_campaign_now Fehler: {e}")
            return f"Fehler beim Senden der Kampagne: {e}"
