import requests
import concurrent.futures
from backend.utils.helpers import log
from backend.utils.constants import WOS_COLLECTIONS, JCR_CATEGORIES

class WoSService:
    def __init__(self, api_key):
        self.api_key = (api_key or "").strip()
        self.headers = {"X-ApiKey": self.api_key} if self.api_key else {}
        self.base_url = "https://api.clarivate.com/apis/wos-starter/v1"

    def get_journal_data(self, issn):
        """
        Orchestrator for WoS data collection.
        Returns a dictionary compatible with the frontend/report requirements.
        """
        if not self.api_key:
            return {"found": False, "source": None, "error": "API Key de WoS no configurada."}
            
        log(f"INFO:Consultando WoS Starter API para ISSN {issn}...")
        
        collections = self.get_collections(issn, None)
        categories_names = self.get_categories(issn, None)
        retracted_count = self.get_retracted_count(issn, None)
        
        # Format categories for the report (similar to Scopus quartiles structure if possible, 
        # but WoS Starter doesn't give quartiles directly without a full JCR API)
        categories = [{"name": cat, "quartile": "[MANUAL]", "rank": "[MANUAL]"} for cat in categories_names]
        
        return {
            "found": True,
            "source": "wos_starter_api",
            "collections": collections,
            "categories": categories,
            "retracted_count": retracted_count if retracted_count >= 0 else 0
        }

    def get_collections(self, eissn, issn_print):
        if not self.api_key: return []
        issn_val = eissn or issn_print
        if not issn_val: return []
        
        def check_collection(edn_code, edn_name):
            query = f'IS={{{issn_val}}} AND EDN=="{edn_code}"'
            try:
                resp = requests.get(f"{self.base_url}/documents", headers=self.headers, params={"q": query, "limit": 1}, timeout=10)
                if resp.status_code == 200 and resp.json().get("metadata", {}).get("total", 0) > 0:
                    return edn_name
            except: pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            found = list(filter(None, executor.map(lambda c: check_collection(*c), WOS_COLLECTIONS.items())))
        return found

    def get_categories(self, eissn, issn_print):
        if not self.api_key: return []
        issn_val = eissn or issn_print
        if not issn_val: return []
        
        def check_category(cat):
            query = f'IS={{{issn_val}}} AND TASCA="{cat}"'
            try:
                resp = requests.get(f"{self.base_url}/documents", headers=self.headers, params={"q": query, "limit": 1}, timeout=7)
                if resp.status_code == 200 and resp.json().get("metadata", {}).get("total", 0) > 0:
                    return cat
            except: pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            found = list(filter(None, executor.map(check_category, JCR_CATEGORIES)))
        return found

    def get_retracted_count(self, eissn, issn_print):
        if not self.api_key: return -1
        issn_val = eissn or issn_print
        if not issn_val: return -1
        
        query = f'IS={{{issn_val}}} AND DT=="RETRACTION"'
        try:
            resp = requests.get(f"{self.base_url}/documents", headers=self.headers, params={"q": query, "limit": 1}, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("metadata", {}).get("total", 0)
        except: pass
        return -1
