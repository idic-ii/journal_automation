import requests
import re
import pandas as pd
import time
from io import StringIO
from bs4 import BeautifulSoup
from backend.utils.helpers import log

PREDATORY_SHEET_ID = "1Qa1lAlSbl7iiKddYINNsDB4wxI7uUA4IVseeLnCc5U4"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}

class IntegrityService:
    @staticmethod
    def _normalize(text):
        if not text: return ""
        text = str(text).lower().strip()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _fetch_html(url):
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=20)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
        except: pass
        return None

    @staticmethod
    def _parse_bealls(url):
        result = {}
        soup = IntegrityService._fetch_html(url)
        if not soup: return result
        for a in soup.select("ul li a[href]"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if text and len(text) > 3 and href.startswith("http") and "beallslist.net" not in href:
                clean = re.sub(r'\s*\(.*?\)', '', text).strip()
                if clean:
                    result[IntegrityService._normalize(clean)] = clean
        return result

    @staticmethod
    def _parse_predatory_sheet():
        result = {}
        url = f"https://docs.google.com/spreadsheets/d/{PREDATORY_SHEET_ID}/export?format=csv"
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=30)
            if resp.status_code != 200: return result
            df = pd.read_csv(StringIO(resp.text), dtype=str, header=None)
            for val in df.values.flatten():
                if val is None or pd.isna(val): continue
                val = str(val).strip()
                if not val or re.fullmatch(r'\d+', val) or len(val) < 4: continue
                result[IntegrityService._normalize(val)] = val
        except: pass
        return result

    @staticmethod
    def check_predatory(journal_name, publisher):
        """
        Verifica si la revista o editorial figuran en listas de revistas predatorias.
        Utiliza scraping de Beall's List y una hoja de cálculo de Google.
        """
        log("INFO:Consultando listas de integridad (Beall's List y otros)...")
        
        publishers_list = IntegrityService._parse_bealls("https://beallslist.net/")
        time.sleep(0.5)
        standalone_list = IntegrityService._parse_bealls("https://beallslist.net/standalone-journals/")
        time.sleep(0.5)
        predatory_list  = IntegrityService._parse_predatory_sheet()

        found = []
        if journal_name:
            norm_j = IntegrityService._normalize(journal_name)
            if predatory_list.get(norm_j):
                found.append("Lista 1 (predatoryjournals.org)")
            if standalone_list.get(norm_j):
                found.append("Lista 2 - Beall's (journal)")
        
        if publisher:
            norm_p = IntegrityService._normalize(publisher)
            m = publishers_list.get(norm_p)
            if m: 
                found.append(f"Lista 2 - Beall's (publisher: {m})")
        
        return found
