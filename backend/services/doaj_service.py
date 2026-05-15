import requests
from backend.utils.helpers import log

class DoajService:
    """Consulta la API pública de DOAJ para verificar el registro de una revista."""
    
    BASE_URL = "https://doaj.org/api/search/journals"

    @staticmethod
    def check_journal(issn=None, eissn=None):
        """
        Consulta DOAJ por ISSN o E-ISSN.
        Retorna un diccionario con los datos relevantes o None si no se encuentra.
        """
        issn_to_try = eissn or issn
        if not issn_to_try:
            return {"in_doaj": False, "status": "error", "message": "Sin ISSN para consultar"}

        url = f"{DoajService.BASE_URL}/issn:{issn_to_try}"
        
        try:
            log(f"INFO: Consultando DOAJ para ISSN {issn_to_try}...")
            resp = requests.get(url, timeout=12)
            
            if resp.status_code != 200:
                log(f"WARN: DOAJ respondió con código {resp.status_code}")
                return {
                    "in_doaj": False,
                    "status": "error",
                    "message": f"DOAJ respondió con código {resp.status_code}"
                }

            data = resp.json()
            
            if data.get("total", 0) == 0:
                return {
                    "in_doaj": False,
                    "status": "ok",
                    "message": "No registrada en DOAJ"
                }

            # Extraer datos del primer resultado
            result = data["results"][0]
            bib = result.get("bibjson", {})
            admin = result.get("admin", {})
            
            # APC
            apc_info = bib.get("apc", {})
            apc_str = ""
            if apc_info.get("has_apc"):
                max_apc = apc_info.get("max", [{}])
                if max_apc:
                    price = max_apc[0].get("price", "")
                    currency = max_apc[0].get("currency", "")
                    apc_str = f"{price} {currency}" if price else "Sí (monto no especificado)"
            else:
                apc_str = "Sin APC"
            
            # Licencias
            licenses = bib.get("license", [])
            license_types = [lic.get("type", "") for lic in licenses if lic.get("type")]
            
            # Revisión editorial
            editorial = bib.get("editorial", {})
            review_process = editorial.get("review_process", [])
            
            # Preservación
            preservation = bib.get("preservation", {})
            preservation_services = preservation.get("service", []) if preservation.get("has_preservation") else []
            
            # Detección de plagio
            plagiarism = bib.get("plagiarism", {})
            has_plagiarism_detection = plagiarism.get("detection", False)
            
            # Tiempo de publicación
            pub_time_weeks = bib.get("publication_time_weeks", None)
            
            # DOAJ Seal (admin.ticked)
            doaj_seal = admin.get("ticked", False)
            
            # Publisher
            publisher_info = bib.get("publisher", {})
            publisher_name = publisher_info.get("name", "")
            publisher_country = publisher_info.get("country", "")
            
            # OA Start
            oa_start = bib.get("oa_start", None)
            
            # BOAI compliance
            boai = bib.get("boai", False)
            
            # Keywords
            keywords = bib.get("keywords", [])

            # Refs
            refs = bib.get("ref", {})
            journal_url = refs.get("journal", "")

            return {
                "in_doaj": True,
                "status": "ok",
                "doaj_seal": doaj_seal,
                "title": bib.get("title", ""),
                "journal_url": journal_url,
                "apc": apc_str,
                "licenses": license_types,
                "review_process": review_process,
                "preservation": preservation_services,
                "plagiarism_detection": has_plagiarism_detection,
                "pub_time_weeks": pub_time_weeks,
                "publisher": publisher_name,
                "publisher_country": publisher_country,
                "oa_start": oa_start,
                "boai_compliant": boai,
                "keywords": keywords,
                "last_review": admin.get("last_full_review", ""),
            }

        except requests.exceptions.Timeout:
            log("WARN: Timeout al consultar DOAJ")
            return {
                "in_doaj": False,
                "status": "timeout",
                "message": "DOAJ no respondió en el tiempo esperado"
            }
        except Exception as e:
            log(f"WARN: Error al consultar DOAJ: {str(e)}")
            return {
                "in_doaj": False,
                "status": "error",
                "message": f"Error: {str(e)}"
            }
