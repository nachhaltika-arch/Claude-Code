import os
import httpx


async def check_google_business(company_name: str, city: str) -> dict:
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return {"claimed": False, "place_id": None, "rating": None, "ratings_total": None}
    try:
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": f"{company_name} {city}",
            "inputtype": "textquery",
            "fields": "name,place_id,rating,user_ratings_total",
            "key": api_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5)
            data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return {"claimed": False, "place_id": None, "rating": None, "ratings_total": None}
        first = candidates[0]
        return {
            "claimed": True,
            "place_id": first.get("place_id"),
            "rating": first.get("rating"),
            "ratings_total": first.get("user_ratings_total"),
        }
    except Exception:
        return {"claimed": False, "place_id": None, "rating": None, "ratings_total": None}
