import sys
import json
import os

# Ensure absolute imports work when called as a script
from backend.services.scopus_service import ScopusService
from backend.services.wos_service import WoSService
from backend.services.integrity_service import IntegrityService
from backend.services.chart_service import ChartService
from backend.services.report_service import ReportService
from backend.utils.helpers import log

def handle_collect(params):
    """Real-time data collection mode."""
    scopus = ScopusService(params.get("api_key"))
    wos = WoSService(params.get("wos_api_key"))
    integrity = IntegrityService()
    
    eissn = params.get("eissn")
    issn_print = params.get("issn")
    
    # 1. Metadata
    log("STEP:metadata")
    meta = scopus.get_journal_metadata(eissn or issn_print)
    if not meta:
        # Try with the other ISSN if available
        meta = scopus.get_journal_metadata(issn_print or eissn)
    
    if not meta:
        log("ERROR:No se encontró la revista en Scopus.")
        return
        
    log(f"DATA:{json.dumps({'_key': 'meta', **meta})}")

    # 2. Document Count
    log("STEP:total_docs")
    total_docs = scopus.get_total_docs(meta["source_id"])
    log(f"DATA:{json.dumps({'_key': 'total_docs', 'value': total_docs})}")

    # 3. Retractions (Scopus)
    log("STEP:retracted_scopus")
    retracted = scopus.get_retracted_count(meta["source_id"])
    log(f"DATA:{json.dumps({'_key': 'retracted_scopus', 'value': retracted})}")

    # 4. Integrity Hits
    log("STEP:predatory")
    hits = integrity.check_predatory(meta["journal"], meta["publisher"])
    log(f"DATA:{json.dumps({'_key': 'predatory', 'value': hits})}")

    # 4.1 Discontinued Check
    log("STEP:discontinued")
    disc_data = integrity.check_discontinued(meta.get("issn_print"), meta.get("eissn"))
    if disc_data:
        log(f"DATA:{json.dumps({'_key': 'discontinued', 'value': disc_data})}")

    # 5. Production by Year
    log("STEP:pubs_by_year")
    pubs_year = scopus.get_publications_by_year(meta["source_id"])
    log(f"DATA:{json.dumps({'_key': 'pubs_by_year', 'value': pubs_year})}")

    # 6. Production by Country
    log("STEP:pubs_by_country")
    pubs_country = scopus.get_publications_by_country(meta["source_id"])
    log(f"DATA:{json.dumps({'_key': 'pubs_by_country', 'value': pubs_country})}")

    # 7. WoS Data
    log("STEP:wos_data")
    wos_data = wos.get_journal_data(eissn or issn_print)
    log(f"DATA:{json.dumps({'_key': 'wos_collections', 'value': wos_data.get('collections', [])})}")
    log(f"DATA:{json.dumps({'_key': 'wos_categories', 'value': wos_data.get('categories', [])})}")
    log(f"DATA:{json.dumps({'_key': 'retracted_wos', 'value': wos_data.get('retracted_count', 0)})}")

    log("STEP:done")
    log("INFO:Recolección completada.")

def handle_generate(params):
    """Document generation mode."""
    chart_service = ChartService()
    report_service = ReportService()
    
    report_data = params.get("report_data", {})
    meta = report_data.get("meta", {}).copy() # Use copy to avoid side effects
    
    # Merge all editable and collected fields into meta for ReportService
    # This ensures wos_categories, wos_collections, predatory, etc. are reachable inside meta
    for key in ["wos_collections", "wos_categories", "wos_quartiles", "wos_collections_manual", 
                "apc", "pub_time", "retracted_wos", "retracted_wos_manual", "concl_metrics", "predatory", "discontinued"]:
        if key in report_data:
            meta[key] = report_data[key]
        elif key not in meta and key in report_data: # Just in case
            meta[key] = report_data[key]

    # Special case for homepage override
    if report_data.get("homepage"):
        meta["homepage"] = report_data["homepage"]
    
    # Generate charts
    log("INFO:Generando gráficos...")
    year_chart = chart_service.generate_year_chart(report_data.get("pubs_by_year", {}))
    country_chart = chart_service.generate_country_chart(report_data.get("pubs_by_country", []))
    
    # Define output path
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    safe_name = "".join(x for x in meta.get("journal", "report") if x.isalnum() or x in " -_").strip()
    filename = f"Informe_{safe_name}.docx"
    # Use output_file if provided by main.py, otherwise fallback to default
    output_path = params.get("output_file") or os.path.join(output_dir, filename)
    
    # Generate Word
    log("INFO:Construyendo documento Word...")
    report_service.generate_word_report(
        meta=meta,
        pubs_by_year=report_data.get("pubs_by_year", {}),
        total_docs=report_data.get("total_docs", 0),
        retracted_scopus=report_data.get("retracted_scopus", 0),
        predatory_hits=report_data.get("predatory", []),
        year_chart_buf=year_chart,
        country_chart_buf=country_chart,
        pubs_by_country=report_data.get("pubs_by_country", []),
        output_file=output_path,
        nro_informe=params.get("nro_informe", "[COMPLETAR]"),
        institucion=params.get("institucion", []),
        retracted_wos=report_data.get("retracted_wos", 0)
    )
    
    print(f"REPORT_FINISHED:{output_path}")

if __name__ == "__main__":
    # Read params from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
        params = json.loads(input_data)
    except Exception as e:
        log(f"ERROR:Fallo al leer parámetros JSON: {e}")
        sys.exit(1)
        
    mode = params.get("mode", "collect")
    if mode == "collect":
        handle_collect(params)
    elif mode == "generate":
        # Log for debugging path issues
        if params.get("output_file"):
            log(f"INFO:Generando reporte en ruta específica: {params.get('output_file')}")
        handle_generate(params)
