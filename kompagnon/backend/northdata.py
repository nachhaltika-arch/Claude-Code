"""
North Data API helper — fetches Geschäftsführer / Vorstand / Inhaber for a company.
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

_BASE = "https://www.northdata.de/_api/company/v1/company"
_TARGET_ROLES = {"geschäftsführer", "vorstand", "inhaber"}


def _match_role(role_str: str) -> bool:
    if not role_str:
        return False
    low = role_str.lower()
    return any(r in low for r in _TARGET_ROLES)


def _extract_name(relation: dict) -> str:
    """Try common North Data name shapes and return 'First Last' or ''."""
    person = relation.get("person") or {}

    # Shape 1: person.name.firstName / .lastName
    name_obj = person.get("name") or {}
    first = name_obj.get("firstName", "").strip()
    last = name_obj.get("lastName", "").strip()
    if first or last:
        return f"{first} {last}".strip()

    # Shape 2: person.firstName / .lastName (flat)
    first = person.get("firstName", "").strip()
    last = person.get("lastName", "").strip()
    if first or last:
        return f"{first} {last}".strip()

    # Shape 3: relation.name (plain string)
    name_str = relation.get("name", "").strip()
    return name_str


async def fetch_geschaeftsfuehrer(company_name: str, city: str = "") -> str:
    """
    Query North Data for the first Geschäftsführer/Vorstand/Inhaber of *company_name*.

    Returns the full name as a string, or "" if not found / API unavailable.
    """
    api_key = os.getenv("NORTHDATA_API_KEY", "")
    if not api_key:
        logger.debug("NORTHDATA_API_KEY not set — skipping")
        return ""

    params: dict = {"name": company_name}
    if city:
        params["address"] = city

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _BASE,
                params=params,
                headers={"X-Api-Key": api_key},
            )
            if resp.status_code != 200:
                logger.debug("NorthData HTTP %s for %r", resp.status_code, company_name)
                return ""

            data = resp.json()

        # Response may wrap the company under "company" key or be the object itself
        company = data.get("company") or data

        relations = company.get("relations") or []

        for rel in relations:
            # Role may live at rel["role"] or inside rel["roles"] list
            role_str = rel.get("role", "")
            if _match_role(role_str):
                name = _extract_name(rel)
                if name:
                    return name

            for role_entry in rel.get("roles") or []:
                if isinstance(role_entry, dict):
                    role_str = role_entry.get("role", "")
                elif isinstance(role_entry, str):
                    role_str = role_entry
                else:
                    continue
                if _match_role(role_str):
                    name = _extract_name(rel)
                    if name:
                        return name

    except Exception as exc:
        logger.debug("NorthData error for %r: %s", company_name, exc)

    return ""
