import requests
import concurrent.futures
from backend.utils.helpers import log, fmt_issn, percentile_to_quartile, get_asjc_names
from backend.utils.constants import COUNTRIES_TO_CHECK
from datetime import date
import time

class ScopusService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
        self.base_url = "https://api.elsevier.com/content/search/scopus"

    def get_article_and_journal_from_id(self, scopus_id):
        url = f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id.strip()}"
        params = {"field": "dc:title,prism:publicationName,prism:issn,prism:eIssn,dc:creator,prism:coverDate,source-id,prism:doi"}
        resp = requests.get(url, headers=self.headers, params=params, timeout=20)
        
        if resp.status_code != 200:
            raise RuntimeError(f"Error Scopus ID {scopus_id}: {resp.status_code}")
            
        coredata = resp.json().get("abstracts-retrieval-response", {}).get("coredata", {})
        eissn = fmt_issn(coredata.get("prism:eIssn", ""))
        issn_print = fmt_issn(coredata.get("prism:issn", ""))
        
        return {
            "article_title":  coredata.get("dc:title", "N/A"),
            "article_doi":    coredata.get("prism:doi", ""),
            "article_date":   coredata.get("prism:coverDate", ""),
            "article_author": coredata.get("dc:creator", ""),
            "journal_name":   coredata.get("prism:publicationName", "N/A"),
            "issn_print":     issn_print,
            "eissn":          eissn,
            "source_id":      str(coredata.get("source-id", "")),
            "issn_for_lookup": eissn or issn_print
        }

    def get_journal_metadata(self, issn_or_source_id):
        # Determine if it's a source-id or ISSN
        if str(issn_or_source_id).isdigit():
            url = f"https://api.elsevier.com/content/serial/title/sourceid/{issn_or_source_id}"
        else:
            url = f"https://api.elsevier.com/content/serial/title/issn/{issn_or_source_id}"
            
        params = {"view": "CITESCORE"}
        resp = requests.get(url, headers=self.headers, params=params, timeout=20)
        
        if resp.status_code != 200:
            log(f"WARN:Error Metadata {issn_or_source_id}: {resp.status_code}")
            return None
            
        entry_list = resp.json().get("serial-metadata-response", {}).get("entry", [])
        if not entry_list: return None
        entry = entry_list[0]
        
        homepage = scopus_link = ""
        for link in entry.get("link", []):
            ref = link.get("@ref", "")
            if ref == "homepage": homepage = link.get("@href", "")
            elif ref == "scopus-source": scopus_link = link.get("@href", "")

        cs_block = entry.get("citeScoreYearInfoList", {})
        cs_value = cs_block.get("citeScoreCurrentMetric", "")
        cs_year  = cs_block.get("citeScoreCurrentMetricYear", "")

        cs_year_list = cs_block.get("citeScoreYearInfo", [])
        if isinstance(cs_year_list, dict): cs_year_list = [cs_year_list]
        
        target = None
        for y in cs_year_list:
            if y.get("@year") == cs_year and y.get("@status") == "Complete":
                target = y; break
        if not target:
            for y in cs_year_list:
                if y.get("@status") == "Complete":
                    target = y; break

        subject_ranks = []
        if target:
            try:
                subject_ranks = target["citeScoreInformationList"][0]["citeScoreInfo"][0]["citeScoreSubjectRank"]
                if isinstance(subject_ranks, dict): subject_ranks = [subject_ranks]
            except: pass

        quartiles_by_area = {}
        for r in subject_ranks:
            code = r.get("subjectCode", "")
            pct  = r.get("percentile", "")
            cat, subarea = get_asjc_names(code)
            if cat not in quartiles_by_area: quartiles_by_area[cat] = []
            quartiles_by_area[cat].append({
                "subarea":   subarea,
                "cuartil":   percentile_to_quartile(pct),
                "percentil": pct,
            })

        return {
            "journal":         entry.get("dc:title", "N/A"),
            "issn_print":      entry.get("prism:issn", ""),
            "eissn":           entry.get("prism:eIssn", ""),
            "publisher":       entry.get("dc:publisher", "N/A"),
            "homepage":        homepage,
            "scopus_link":     scopus_link,
            "coverage_start":  entry.get("coverageStartYear", "N/A"),
            "coverage_end":    entry.get("coverageEndYear", "present"),
            "citescore_value": cs_value,
            "citescore_year":  cs_year,
            "source_id":       entry.get("source-id", ""),
            "quartiles":       quartiles_by_area
        }

    def get_total_docs(self, source_id):
        params = {"query": f"SOURCE-ID({source_id})", "count": 1, "field": "dc:title"}
        for attempt in range(3):
            try:
                resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
                if resp.status_code == 200:
                    return int(resp.json().get("search-results", {}).get("opensearch:totalResults", 0))
                elif resp.status_code == 429:
                    time.sleep(2 ** (attempt + 1))
                    continue
            except: pass
        return 0

    def get_publications_by_year(self, source_id, start_year=None, end_year=None):
        if not start_year: start_year = date.today().year - 10
        if not end_year: end_year = date.today().year
        
        results = {}
        MAX_RETRIES = 3

        def fetch_year(y):
            query = f"SOURCE-ID({source_id}) AND PUBYEAR = {y}"
            params = {"query": query, "count": 1, "field": "dc:title"}
            for attempt in range(MAX_RETRIES):
                try:
                    resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=20)
                    if resp.status_code == 200:
                        total = int(resp.json().get("search-results", {}).get("opensearch:totalResults", 0))
                        return (y, total)
                    elif resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        log(f"WARN: Rate limited (429) for year {y}, retrying in {wait}s")
                        time.sleep(wait)
                        continue
                except:
                    time.sleep(1)
                    continue
            return (y, 0)

        years_range = range(start_year, end_year + 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for y_data in executor.map(fetch_year, years_range):
                results[str(y_data[0])] = y_data[1]
        return results

    def get_publications_by_country(self, source_id, top_n=15):
        def fetch_country(c):
            query = f'SOURCE-ID({source_id}) AND AFFILCOUNTRY("{c}")'
            params = {"query": query, "count": 1, "field": "dc:title"}
            for attempt in range(3):
                try:
                    resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                    if resp.status_code == 200:
                        total = int(resp.json().get("search-results", {}).get("opensearch:totalResults", 0))
                        return {"country": c, "count": total} if total > 0 else None
                    elif resp.status_code == 429:
                        time.sleep(2 ** (attempt + 1))
                        continue
                except:
                    time.sleep(1)
                    continue
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            full_list = list(filter(None, executor.map(fetch_country, COUNTRIES_TO_CHECK)))
        
        full_list.sort(key=lambda x: x["count"], reverse=True)
        return full_list[:top_n]

    def get_retracted_count(self, source_id):
        params = {"query": f'SOURCE-ID({source_id}) AND DOCTYPE("tb")', "count": 1, "field": "dc:title"}
        for attempt in range(3):
            try:
                resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
                if resp.status_code == 200:
                    return int(resp.json().get("search-results", {}).get("opensearch:totalResults", 0))
                elif resp.status_code == 429:
                    time.sleep(2 ** (attempt + 1))
                    continue
            except: pass
        return 0
