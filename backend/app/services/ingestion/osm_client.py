import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OSMClient:
    """Client for OpenStreetMap Overpass API"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch_pois_in_radius(self, lat: float, lon: float, radius_meters: float) -> List[Dict[str, Any]]:
        """
        Fetches POIs (amenities, historic, tourism, public_transport) within a radius.
        """
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          node["amenity"](around:{radius_meters},{lat},{lon});
          way["amenity"](around:{radius_meters},{lat},{lon});
          node["historic"](around:{radius_meters},{lat},{lon});
          node["tourism"](around:{radius_meters},{lat},{lon});
          node["public_transport"](around:{radius_meters},{lat},{lon});
        );
        out center;
        """
        return self._execute_query(query)

    def fetch_businesses_in_radius(self, lat: float, lon: float, radius_meters: float) -> List[Dict[str, Any]]:
        """
        Fetches businesses (shop, office, craft, specific amenities) within a radius.
        """
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          node["shop"](around:{radius_meters},{lat},{lon});
          way["shop"](around:{radius_meters},{lat},{lon});
          node["office"](around:{radius_meters},{lat},{lon});
          node["craft"](around:{radius_meters},{lat},{lon});
          node["amenity"~"restaurant|cafe|fast_food|bar|pub|pharmacy|clinic|bank"](around:{radius_meters},{lat},{lon});
        );
        out center;
        """
        return self._execute_query(query)

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "GramVyaparBackend/1.0 (contact@gramvyapar.example.com)",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            # Send as standard form data where key is 'data' and value is query
            response = httpx.post(self.OVERPASS_URL, data={"data": query}, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("elements", [])

        except httpx.HTTPError as e:
            logger.error(f"HTTP exception fetching data from OSM: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching data from OSM: {e}")
            return []


