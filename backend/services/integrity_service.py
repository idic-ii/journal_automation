import requests
import re
import pandas as pd
import time
import os
from io import StringIO
from bs4 import BeautifulSoup
from backend.utils.helpers import log

PREDATORY_JOURNAL_SHEET_ID = "1Qa1lAlSbl7iiKddYINNsDB4wxI7uUA4IVseeLnCc5U4"
PREDATORY_PUBLISHER_SHEET_ID = "1BHM4aJljhbOAzSpkX1kXDUEvy6vxREZu5WJaDH6M1Vk"
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
            log(f"WARN: {url} respondió con código {resp.status_code}")
        except requests.exceptions.Timeout:
            log(f"WARN: Timeout al consultar {url}")
        except Exception as e:
            log(f"WARN: Error al consultar {url}: {str(e)}")
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
                # Borrar paréntesis y contenido (específico para Beall's)
                clean = re.sub(r'\s*\([^)]*\)', '', text).strip()
                if clean:
                    result[IntegrityService._normalize(clean)] = clean
        return result

    @staticmethod
    def _parse_google_sheet(sheet_id):
        """Parsea una hoja de Google Sheets en formato CSV."""
        result = {}
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=30)
            if resp.status_code != 200: return result
            df = pd.read_csv(StringIO(resp.text), dtype=str, header=None)
            for val in df.values.flatten():
                if val is None or pd.isna(val) or not isinstance(val, str): continue
                val = str(val).strip()
                # Filtrar números puros o textos muy cortos
                if not val or re.fullmatch(r'\d+', val) or len(val) < 4: continue
                result[IntegrityService._normalize(val)] = val
        except requests.exceptions.Timeout:
            log(f"WARN: Timeout al descargar Google Sheet {sheet_id}")
        except Exception as e:
            log(f"WARN: Error al parsear Google Sheet {sheet_id}: {str(e)}")
        return result

    @staticmethod
    def check_predatory(journal_name, publisher):
        """
        Verifica si la revista o editorial figuran en listas de revistas predatorias.
        Utiliza scraping de Beall's List y hojas de cálculo de Google (Journals y Publishers).
        """
        log("INFO:Consultando listas de integridad (Beall's y Predatory Sheets)...")
        
        sources_status = {}
        
        # 1. Obtener listas de Beall's
        bealls_publishers = IntegrityService._parse_bealls("https://beallslist.net/")
        sources_status["bealls_publishers"] = "ok" if bealls_publishers else "error"
        time.sleep(0.3)
        bealls_journals   = IntegrityService._parse_bealls("https://beallslist.net/standalone-journals/")
        sources_status["bealls_journals"] = "ok" if bealls_journals else "error"
        time.sleep(0.3)
        
        # 2. Obtener listas de Google Sheets
        predatory_journals   = IntegrityService._parse_google_sheet(PREDATORY_JOURNAL_SHEET_ID)
        sources_status["predatory_journals_sheet"] = "ok" if predatory_journals else "error"
        predatory_publishers = IntegrityService._parse_google_sheet(PREDATORY_PUBLISHER_SHEET_ID)
        sources_status["predatory_publishers_sheet"] = "ok" if predatory_publishers else "error"

        found = []
        
        # --- Verificación de la REVISTA ---
        if journal_name:
            norm_j = IntegrityService._normalize(journal_name)
            if predatory_journals.get(norm_j):
                found.append(f"Revista en Lista 1 (predatoryjournals.org)")
            if bealls_journals.get(norm_j):
                found.append(f"Revista en Lista 2 (Beall's Standalone)")
        
        # --- Verificación de la EDITORIAL ---
        if publisher:
            norm_p = IntegrityService._normalize(publisher)
            if predatory_publishers.get(norm_p):
                found.append(f"Editorial en Lista 1 (predatoryjournals.org)")
            m_beall = bealls_publishers.get(norm_p)
            if m_beall:
                found.append(f"Editorial en Lista 2 (Beall's Publisher: {m_beall})")
        
        return {"hits": found, "sources_status": sources_status}

    @staticmethod
    def check_discontinued(issn, eissn):
        """
        Verifica si la revista figura como Inactiva en el Excel de Scopus.
        """
        # Intentar buscar el archivo en backend/data
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, "data", "Revistas_descontinuadas_Scopus.xlsx")
        
        if not os.path.exists(file_path):
            # Buscar cualquier excel en la carpeta si no se llama exactamente así
            data_dir = os.path.join(base_path, "data")
            if os.path.exists(data_dir):
                files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
                if files:
                    file_path = os.path.join(data_dir, files[0])
                else:
                    log(f"WARN: No se encontró archivo Excel de descontinuadas en {data_dir}")
                    return None
            else:
                return None

        try:
            # Leer solo las columnas necesarias
            df = pd.read_excel(file_path, dtype=str)
            
            # Normalizar nombres de columnas (limpiar espacios y saltos de línea)
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            
            def clean(s): 
                if pd.isna(s) or s is None: return ""
                return str(s).strip().replace("-", "")
            
            issn_c = clean(issn)
            eissn_c = clean(eissn)
            
            # Columnas exactas según el excel del usuario
            col_issn = "ISSN"
            col_eissn = "EISSN"
            col_status = "Active or Inactive"
            col_coverage = "Coverage"

            if col_issn not in df.columns or col_status not in df.columns:
                log(f"WARN: Columnas requeridas no encontradas en el Excel. Columnas: {df.columns.tolist()}")
                return None

            # Buscar match
            matches = []
            if issn_c:
                matches.append(df[df[col_issn].apply(clean) == issn_c])
            if eissn_c:
                matches.append(df[df.get(col_eissn, pd.Series()).apply(clean) == eissn_c])
            
            final_match = pd.concat(matches).drop_duplicates() if matches else pd.DataFrame()

            if not final_match.empty:
                row = final_match.iloc[0]
                status = str(row[col_status]).strip()
                if status.lower() == "inactive":
                    return {
                        "is_discontinued": True,
                        "coverage": row.get(col_coverage, "Desconocida")
                    }
            
            return {"is_discontinued": False}
        except Exception as e:
            log(f"ERROR: Fallo al verificar revistas descontinuadas: {e}")
            return None
