import pandas as pd
import os
import re
from backend.utils.helpers import log

class RetractionService:
    _df = None
    _data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "retraction_watch.csv")

    REASONS_MAP = {
 
    # ─── INVESTIGACIONES FORMALES ──────────────────────────────────────────────
    "Investigation by Journal/Publisher": (
        "La editorial o revista está conduciendo una investigación formal sobre la integridad "
        "del artículo antes o después de su publicación."
    ),
    "Investigation by Company/Institution": (
        "La institución o empresa afiliada al autor ha iniciado una investigación oficial "
        "sobre posibles malas prácticas de investigación."
    ),
    "Investigation by Third Party": (
        "Un organismo externo independiente —distinto de la revista, la institución del autor "
        "o la empresa— está llevando a cabo una investigación sobre el artículo."
    ),
    "Investigation by ORI": (
        "La Oficina de Integridad en la Investigación (ORI) de los EE. UU. está investigando "
        "formalmente al autor o al estudio por posible mala conducta científica."
    ),
    "Misconduct - Official Investigation(s) and/or Finding(s)": (
        "Existe una investigación oficial concluida o en curso que ha determinado o está "
        "evaluando mala conducta científica por parte del autor o equipo investigador."
    ),
 
    # ─── PROBLEMAS DE DATOS ───────────────────────────────────────────────────
    "Concerns/Issues about Data": (
        "Se han identificado dudas razonables o inconsistencias en los datos presentados "
        "que comprometen la validez o reproducibilidad de los resultados."
    ),
    "Unreliable Data": (
        "Los datos del estudio no son confiables, ya sea por errores sistemáticos, "
        "manipulación o imposibilidad de verificar su origen."
    ),
    "Falsification/Fabrication of Data": (
        "Los datos han sido alterados intencionalmente o inventados para apoyar "
        "una hipótesis o resultado específico."
    ),
    "Duplication of Data": (
        "Datos de una publicación previa han sido reutilizados en este artículo "
        "sin declaración de dicha reutilización."
    ),
    "Plagiarism of Data": (
        "Los datos presentados han sido tomados de otros estudios sin permiso "
        "ni citación apropiada, presentándolos como datos propios."
    ),
    "Error in Data": (
        "Se han identificado errores técnicos o de cálculo no intencionales "
        "en los datos que afectan los resultados del estudio."
    ),
    "Manipulation of Data": (
        "Los datos han sido modificados de forma deliberada e inapropiada para "
        "producir resultados que no reflejan la realidad observada."
    ),
    "Original Data and/or Images not Provided and/or not Available": (
        "Los autores no han podido o no han querido proporcionar los datos originales "
        "o imágenes que respaldan los resultados publicados."
    ),
 
    # ─── PROBLEMAS DE IMÁGENES ────────────────────────────────────────────────
    "Concerns/Issues about Image": (
        "Se han detectado irregularidades, duplicaciones o manipulaciones sospechosas "
        "en las imágenes o figuras del artículo."
    ),
    "Duplication of/in Image": (
        "Imágenes que ya aparecieron en otras publicaciones han sido utilizadas "
        "en este artículo como si fueran nuevas u originales."
    ),
    "Falsification/Fabrication of Image": (
        "Las imágenes han sido editadas digitalmente o creadas artificialmente "
        "para representar resultados que no existen o no ocurrieron."
    ),
    "Plagiarism of Image": (
        "Se han utilizado imágenes de otros autores o publicaciones presentándolas "
        "como propias, sin permiso ni atribución correspondiente."
    ),
    "Manipulation of Images": (
        "Las imágenes fueron modificadas digitalmente de forma inapropiada, "
        "alterando lo que realmente representan o mostrando resultados engañosos."
    ),
    "Unreliable Image": (
        "Las imágenes del artículo no son confiables, ya sea porque han sido "
        "alteradas, reutilizadas o no corresponden fielmente a los datos reportados."
    ),
    "Error in Image": (
        "Se han detectado errores no intencionados en la presentación, etiquetado "
        "o preparación de las imágenes que afectan la interpretación del estudio."
    ),
 
    # ─── RESULTADOS Y CONCLUSIONES ────────────────────────────────────────────
    "Unreliable Results and/or Conclusions": (
        "Los resultados o conclusiones del estudio no son confiables debido a errores "
        "metodológicos, datos defectuosos o razonamiento incorrecto."
    ),
    "Concerns/Issues about Results and/or Conclusions": (
        "Existen dudas fundadas sobre la validez, exactitud o interpretación "
        "de los resultados o conclusiones reportados."
    ),
    "Results Not Reproducible": (
        "Los resultados del estudio no han podido ser replicados por otros investigadores "
        "bajo condiciones equivalentes, cuestionando su validez."
    ),
    "Error in Results and/or Conclusions": (
        "Se han identificado errores no intencionales en los resultados o conclusiones "
        "que afectan sustancialmente la validez del trabajo."
    ),
    "Falsification/Fabrication of Results": (
        "Los resultados han sido alterados o fabricados deliberadamente para apoyar "
        "afirmaciones que no están respaldadas por los datos reales."
    ),
    "Manipulation of Results": (
        "Los resultados han sido modificados de forma selectiva o inapropiada "
        "para producir conclusiones que no reflejan los datos obtenidos."
    ),
 
    # ─── PLAGIO ───────────────────────────────────────────────────────────────
    "Plagiarism of/in Article": (
        "Porciones sustanciales del texto del artículo han sido copiadas de otras "
        "publicaciones sin la debida atribución o reconocimiento."
    ),
    "Plagiarism of Text": (
        "El texto del artículo reproduce fragmentos de otras fuentes publicadas "
        "sin citar correctamente ni indicar que se trata de material ajeno."
    ),
    "Euphemisms for Plagiarism": (
        "La noticia de retractación usa terminología vaga o eufemística (como 'uso "
        "inapropiado de fuentes') para describir lo que en esencia constituye plagio."
    ),
 
    # ─── DUPLICACIÓN ──────────────────────────────────────────────────────────
    "Duplication of/in Article": (
        "El mismo artículo o partes sustanciales de él han sido publicados en más "
        "de una revista científica sin declaración de publicación previa (publicación redundante)."
    ),
    "Duplication of Text": (
        "Segmentos de texto de una publicación previa del mismo autor han sido "
        "incorporados en este artículo sin indicar su origen (autoplagio)."
    ),
    "Duplication of Content through Error by Journal/Publisher": (
        "La revista o editorial publicó contenido duplicado por error propio en "
        "el proceso editorial, no por conducta deliberada del autor."
    ),
    "Euphemisms for Duplication": (
        "La noticia de retractación emplea términos ambiguos para describir lo "
        "que en esencia es publicación duplicada o redundante."
    ),
    "Salami Slicing": (
        "Los resultados de un único estudio han sido fragmentados artificialmente "
        "en múltiples publicaciones para inflar artificialmente el número de artículos."
    ),
 
    # ─── REVISIÓN POR PARES ───────────────────────────────────────────────────
    "Concerns/Issues about Peer Review": (
        "Existen indicios de irregularidades en el proceso de revisión por pares "
        "que cuestionan la validez del proceso de evaluación del artículo."
    ),
    "Compromised Peer Review": (
        "El proceso de revisión por pares fue manipulado deliberadamente, por ejemplo "
        "mediante revisores falsos, anillos de revisión o identidades suplantadas."
    ),
    "Taken via Peer Review": (
        "El contenido del artículo fue obtenido o filtrado de forma fraudulenta "
        "durante el proceso de revisión por pares de otro trabajo."
    ),
 
    # ─── AUTORÍA Y AFILIACIÓN ─────────────────────────────────────────────────
    "Concerns/Issues about Authorship/Affiliation": (
        "Se han detectado irregularidades en la lista de autores, como autores "
        "honoríficos, autores fantasma o afiliaciones institucionales incorrectas."
    ),
    "False/Forged Authorship": (
        "Uno o más autores listados no participaron realmente en el estudio, "
        "o sus nombres fueron incluidos sin consentimiento."
    ),
    "False/Forged Affiliation": (
        "La afiliación institucional declarada por uno o más autores es falsa, "
        "exagerada o fue incluida sin autorización de la institución."
    ),
    "Lack of Approval from Author": (
        "El artículo fue sometido o publicado sin el conocimiento o aprobación "
        "explícita de uno o más de los autores firmantes."
    ),
 
    # ─── CONDUCTA INAPROPIADA ─────────────────────────────────────────────────
    "Misconduct by Author": (
        "El autor ha incurrido en mala conducta científica grave, que puede incluir "
        "fraude, fabricación, falsificación u otras violaciones éticas."
    ),
    "Misconduct by Third Party": (
        "Un tercero no perteneciente al equipo autor ni a la institución ha actuado "
        "de forma fraudulenta afectando la integridad del artículo."
    ),
    "Misconduct by Company/Institution": (
        "La empresa o institución vinculada al estudio ha incurrido en conductas "
        "inapropiadas que comprometen la integridad de la investigación."
    ),
    "Euphemisms for Misconduct": (
        "La noticia de retractación emplea lenguaje vago o eufemístico para "
        "describir lo que constituye formalmente mala conducta científica."
    ),
    "Breach of Policy by Author": (
        "El autor ha violado políticas editoriales, éticas o institucionales "
        "relevantes para la publicación del artículo."
    ),
    "Complaints about Author": (
        "Se han recibido quejas formales contra el autor por conducta inapropiada "
        "relacionada con el artículo o la investigación."
    ),
    "Complaints about Third Party": (
        "Se han recibido quejas sobre la conducta de un tercero que afecta "
        "la integridad del artículo publicado."
    ),
    "Complaints about Company/Institution": (
        "Se han presentado quejas formales contra la institución o empresa vinculada "
        "al estudio por conducta inapropiada relacionada con la investigación."
    ),
 
    # ─── ÉTICA Y CONSENTIMIENTO ───────────────────────────────────────────────
    "Ethical Violations by Author": (
        "El autor ha cometido violaciones a los principios éticos fundamentales "
        "de la investigación científica, ya sea con humanos, animales o datos."
    ),
    "Ethical Violations by Company/Institution/Third Party": (
        "La empresa, institución o un tercero ha cometido violaciones éticas "
        "que comprometen la integridad del estudio publicado."
    ),
    "Lack of IRB/IACUC Approval and/or Compliance": (
        "El estudio no contó con la aprobación requerida del comité de ética "
        "institucional para investigación con humanos (IRB) o animales (IACUC)."
    ),
    "Informed/Patient Consent - None/Withdrawn": (
        "El estudio no obtuvo el consentimiento informado de los participantes, "
        "o dicho consentimiento fue revocado con posterioridad a la publicación."
    ),
    "Concerns/Issues about Human Subject Welfare": (
        "Existen preocupaciones sobre el trato, la seguridad o el bienestar "
        "de los sujetos humanos involucrados en la investigación."
    ),
    "Concerns/Issues about Animal Welfare": (
        "Existen preocupaciones sobre el trato, los procedimientos o el bienestar "
        "de los animales utilizados en la investigación."
    ),
 
    # ─── ERRORES NO INTENCIONALES ─────────────────────────────────────────────
    "Error in Analyses": (
        "Se han identificado errores no intencionales en los análisis estadísticos "
        "o cuantitativos que afectan la validez de los resultados reportados."
    ),
    "Error in Methods": (
        "Los métodos descritos contienen errores que afectan la replicabilidad "
        "o validez del experimento o análisis realizado."
    ),
    "Error in Text": (
        "El cuerpo del artículo contiene errores textuales que afectan "
        "de forma sustancial la comprensión o precisión del trabajo."
    ),
    "Error in Materials": (
        "Se han detectado errores en la descripción o uso de los materiales "
        "del estudio que afectan la reproducibilidad o validez del experimento."
    ),
    "Error in Cell Lines/Tissues": (
        "Las líneas celulares o tejidos utilizados en el estudio contenían errores "
        "de identificación, contaminación o uso incorrecto que invalidan los resultados."
    ),
    "Error by Journal/Publisher": (
        "El error que motivó la retractación o corrección fue cometido por "
        "la editorial o revista, no por los autores del artículo."
    ),
    "Error by Third Party": (
        "El error que compromete la integridad del artículo fue cometido "
        "por un tercero involucrado en la investigación o publicación."
    ),
 
    # ─── MÉTODOS Y MATERIALES ─────────────────────────────────────────────────
    "Concerns/Issues about Methods": (
        "Existen dudas fundadas sobre la validez, idoneidad o correcta aplicación "
        "de los métodos empleados en el estudio."
    ),
    "Contamination of Cell Lines/Tissues": (
        "Las líneas celulares o tejidos usados en el estudio estaban contaminados, "
        "lo que compromete la validez de los resultados biológicos reportados."
    ),
    "Contamination of Materials": (
        "Los materiales empleados en el experimento estaban contaminados, "
        "invalidando los resultados o comprometiendo su reproducibilidad."
    ),
    "Sabotage of Materials/Methods": (
        "Alguien manipuló deliberadamente los materiales o métodos del estudio "
        "con intención de sabotear la investigación o sus resultados."
    ),
 
    # ─── REFERENCIAS Y CITACIONES ─────────────────────────────────────────────
    "Concerns/Issues about Referencing/Attributions": (
        "Existen problemas con la citación de fuentes, ya sea por omisiones, "
        "atribuciones incorrectas o referencias manipuladas."
    ),
    "Cites Retracted Work": (
        "El artículo cita como válido un trabajo que ya fue retractado, "
        "comprometiendo potencialmente sus propias conclusiones."
    ),
 
    # ─── PAPEL DE MOLINO (PAPER MILL) ─────────────────────────────────────────
    "Paper Mill": (
        "El artículo fue producido por una 'fábrica de artículos' (paper mill): "
        "una organización que genera y vende trabajos científicos fraudulentos."
    ),
 
    # ─── CONTENIDO GENERADO POR COMPUTADORA ──────────────────────────────────
    "Computer-Aided Content or Computer-Generated Content": (
        "El artículo contiene texto, datos o resultados generados total o parcialmente "
        "por inteligencia artificial u otras herramientas automatizadas sin la debida declaración."
    ),
 
    # ─── EDITOR DESHONESTO ────────────────────────────────────────────────────
    "Rogue Editor": (
        "Un editor actuó de forma fraudulenta o sin autorización, manipulando "
        "el proceso editorial para publicar artículos sin revisión legítima."
    ),
 
    # ─── CONFLICTO DE INTERÉS ─────────────────────────────────────────────────
    "Conflict of Interest": (
        "Existen intereses financieros, personales o institucionales no declarados "
        "que podrían sesgar los resultados o conclusiones del estudio."
    ),
 
    # ─── PROBLEMAS LEGALES Y DERECHOS ─────────────────────────────────────────
    "Copyright Claims": (
        "El artículo o partes de él infringen derechos de autor de terceros, "
        "lo que ha generado una reclamación legal de propiedad intelectual."
    ),
    "Legal Reasons and/or Threats": (
        "Razones legales, demandas judiciales o amenazas de litigio motivaron "
        "la retractación del artículo independientemente de su mérito científico."
    ),
    "Civil Proceedings": (
        "Se han iniciado procedimientos legales civiles relacionados con "
        "el contenido, autoría o publicación del artículo."
    ),
    "Criminal Proceedings": (
        "Se han iniciado acciones penales relacionadas con el artículo, "
        "ya sea por fraude científico, falsificación u otros delitos."
    ),
    "Transfer of Copyright and/or Ownership": (
        "La retractación se originó por disputas o cambios en la titularidad "
        "de los derechos de autor o propiedad del artículo."
    ),
    "Publishing Ban": (
        "Uno o más autores están sujetos a una prohibición formal de publicación "
        "impuesta por una institución, editorial o comité de ética."
    ),
 
    # ─── OBJECIONES ───────────────────────────────────────────────────────────
    "Objections by Author(s)": (
        "Uno o más autores han presentado objeciones formales a la publicación, "
        "a los términos de la retractación o al contenido del artículo."
    ),
    "Objections by Third Party": (
        "Un tercero externo al equipo autor ha planteado objeciones formales "
        "sobre el artículo, su contenido o su proceso de publicación."
    ),
    "Objections by Company/Institution": (
        "Una empresa o institución vinculada ha presentado objeciones formales "
        "respecto al artículo o a las condiciones de su publicación."
    ),
 
    # ─── TERCEROS ─────────────────────────────────────────────────────────────
    "Concerns/Issues about Third Party Involvement": (
        "Existen preocupaciones sobre el rol o influencia de un tercero externo "
        "al equipo investigador en el diseño, datos o publicación del estudio."
    ),
    "Lack of Approval from Third Party": (
        "El artículo fue publicado sin obtener la aprobación necesaria "
        "de un tercero cuyo consentimiento era requerido."
    ),
    "Lack of Approval from Company/Institution": (
        "La empresa o institución vinculada no autorizó la publicación "
        "del artículo o de los datos incluidos en él."
    ),
 
    # ─── COMUNICACIÓN Y RESPUESTA ─────────────────────────────────────────────
    "Author Unresponsive": (
        "Los autores no han respondido a las comunicaciones de la editorial "
        "sobre dudas de integridad, lo que imposibilita resolver las preocupaciones."
    ),
    "Miscommunication with/by Author": (
        "Problemas de comunicación con el autor o por parte del autor originaron "
        "errores o malentendidos que motivaron la retractación o corrección."
    ),
    "Miscommunication with/by Journal/Publisher": (
        "Problemas de comunicación interna de la editorial o con ella dieron lugar "
        "a errores en el proceso de publicación o retractación."
    ),
    "Miscommunication with/by Third Party": (
        "Problemas de comunicación con o por parte de un tercero contribuyeron "
        "a errores que motivaron la retractación o corrección del artículo."
    ),
    "Miscommunication with/by Company/Institution": (
        "Problemas de comunicación con la institución o empresa vinculada "
        "al estudio derivaron en errores que afectan la validez de la publicación."
    ),
 
    # ─── ACCIONES EDITORIALES / ADMINISTRATIVAS ───────────────────────────────
    "Concerns/Issues about Article": (
        "Existen preocupaciones generales sobre la integridad, calidad o validez "
        "del artículo que aún no han sido categorizadas con mayor especificidad."
    ),
    "Notice - Limited or No Information": (
        "La noticia de retractación proporciona información mínima o nula "
        "sobre las razones específicas que motivaron la retractación."
    ),
    "Notice - Lack of": (
        "No existe una noticia de retractación formal o pública disponible "
        "que explique las razones de la retractación del artículo."
    ),
    "Notice - Unable to Access via current resources": (
        "La noticia de retractación existe pero no es accesible a través "
        "de los recursos o medios disponibles actualmente."
    ),
    "Date of Article and/or Notice Unknown": (
        "No se puede determinar con certeza la fecha de publicación del artículo "
        "o la fecha de emisión de la noticia de retractación."
    ),
    "Removed": (
        "El artículo fue eliminado de la plataforma o base de datos sin que "
        "se emitiera una retractación formal o se explicaran las razones."
    ),
    "Temporary Removal": (
        "El artículo fue retirado temporalmente de la plataforma editorial "
        "mientras se resuelve una investigación o se corrige un problema identificado."
    ),
    "Retract and Replace": (
        "El artículo original fue retractado y reemplazado simultáneamente "
        "por una versión corregida que subsana los errores identificados."
    ),
    "Upgrade/Update of Prior Notice(s)": (
        "Una noticia editorial previa (corrección o expresión de preocupación) "
        "ha sido actualizada o escalada a una retractación formal."
    ),
    "Updated to Retraction": (
        "Una noticia editorial previa —como una expresión de preocupación o corrección— "
        "ha sido convertida en una retractación formal del artículo."
    ),
    "Updated to Correction": (
        "Una noticia previa ha sido reclasificada como una corrección formal "
        "al determinarse que los errores no justifican una retractación completa."
    ),
    "Updated to Expression of Concern": (
        "Una noticia previa ha sido reclasificada o actualizada a una expresión "
        "de preocupación formal por parte de la editorial."
    ),
    "No Further Action": (
        "Tras la investigación, la editorial determinó que no se requieren "
        "acciones adicionales como retractación o corrección del artículo."
    ),
    "EOC Lifted": (
        "La expresión de preocupación (Expression of Concern) emitida previamente "
        "ha sido levantada al concluirse que las dudas carecen de fundamento."
    ),
    "Nonpayment of Fees and/or Refusal to Pay": (
        "El artículo está sujeto a una disputa o retractación relacionada con "
        "el impago de tarifas editoriales o la negativa a satisfacerlas."
    ),
 
    # ─── RETIRADAS VOLUNTARIAS O ESPECIALES ───────────────────────────────────
    "Withdrawn to Publish in Different Journal": (
        "El artículo fue retirado por el autor para someterse a revisión "
        "y publicarse en una revista diferente."
    ),
    "Withdrawn as Out of Date": (
        "El artículo fue retirado porque su contenido ha quedado desactualizado "
        "o superado por investigaciones más recientes."
    ),
    "Taken from Dissertation/Thesis": (
        "El contenido del artículo fue extraído de una tesis o disertación "
        "sin declarar adecuadamente dicho origen o sin autorización del tutor."
    ),
    "Taken via Translation": (
        "El artículo fue publicado como una traducción de un trabajo previo "
        "sin informar a la revista o sin el consentimiento de los autores originales."
    ),
    "Doing the Right Thing": (
        "Los autores retractaron voluntaria y proactivamente el artículo al detectar "
        "errores propios, aun sin presión externa — acto de integridad científica."
    ),
    "Not Presented at Conference": (
        "El artículo fue publicado como actas de congreso, pero el trabajo "
        "nunca fue realmente presentado en la conferencia indicada."
    ),
    "Hoax Paper": (
        "El artículo fue enviado deliberadamente como una prueba de las debilidades "
        "del proceso editorial, con contenido ficticio o sin mérito científico real."
    ),
 
    # ─── SESGOS ───────────────────────────────────────────────────────────────
    "Bias Issues or Lack of Balance": (
        "El artículo presenta sesgos significativos en su diseño, análisis o conclusiones, "
        "o carece del balance necesario para representar fielmente la evidencia disponible."
    ),
}
    @classmethod
    def _load_data(cls):
        """Carga el CSV de Retraction Watch si no está cargado."""
        if cls._df is None:
            if not os.path.exists(cls._data_path):
                log(f"WARN: Archivo de Retraction Watch no encontrado en {cls._data_path}")
                return None
            try:
                log("INFO: Iniciando carga de base de datos Retraction Watch (64MB)...")
                log("STEP:retraction_watch_loading")
                # Cargamos solo las columnas necesarias para ahorrar memoria
                cols = ["Journal", "Reason", "RetractionDate", "Title", "RetractionNature"]
                cls._df = pd.read_csv(cls._data_path, usecols=cols, dtype=str, low_memory=False)
                # Limpieza básica: rellenar nulos
                cls._df = cls._df.fillna("")
                # Normalizar la columna Journal para búsquedas rápidas
                cls._df["journal_norm"] = cls._df["Journal"].apply(cls._normalize_name)
                log(f"INFO: Base de datos cargada. {len(cls._df)} registros.")
            except Exception as e:
                log(f"ERROR: Fallo al cargar Retraction Watch: {str(e)}")
                return None
        return cls._df

    @staticmethod
    def _normalize_name(name):
        """Normalización estricta para match por nombre."""
        if not name or pd.isna(name): return ""
        
        # Eliminar paréntesis y su contenido (ej: "Journal (AJSCA)" -> "Journal")
        name = re.sub(r'\s*\([^)]*\)', '', str(name)).strip()
        
        # Minúsculas, quitar puntuación, espacios múltiples
        name = name.lower()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        return " ".join(name.split())

    @classmethod
    def _translate_items(cls, items_str):
        """Traduce una cadena de motivos separados por punto y coma."""
        if not items_str: return ""
        parts = [p.strip() for p in items_str.split(";") if p.strip()]
        translated = []
        for p in parts:
            # Buscar coincidencia exacta o parcial en el mapa
            found = False
            for eng, esp in cls.REASONS_MAP.items():
                if eng.lower() in p.lower():
                    translated.append(esp)
                    found = True
                    break
            if not found:
                translated.append(p) # Mantener original si no hay traducción
        return ", ".join(list(dict.fromkeys(translated))) # Deduplicar y unir

    @staticmethod
    def _format_date(date_str):
        """Convierte '2/26/2026 0:00' → '26 de febrero de 2026'."""
        if not date_str or not isinstance(date_str, str):
            return date_str or ""
        MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str.split(" ")[0], "%m/%d/%Y")
            return f"{dt.day} de {MESES[dt.month - 1]} de {dt.year}"
        except Exception:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str.split(" ")[0], "%d/%m/%Y")
                return f"{dt.day} de {MESES[dt.month - 1]} de {dt.year}"
            except Exception:
                return date_str

    @classmethod
    def check_retractions(cls, journal_name):
        """
        Busca retracciones para una revista específica.
        Retorna un resumen estadístico y los ejemplos más recientes.
        """
        df = cls._load_data()
        if df is None: return None

        norm_target = cls._normalize_name(journal_name)
        if not norm_target: return None

        # Filtrar por nombre de revista
        matches = df[df["journal_norm"] == norm_target].copy()
        
        if matches.empty:
            return {"count": 0, "summary": "", "examples": []}

        total_count = len(matches)
        
        # 1. Analizar motivos (Reasons) ORIGINALES
        all_reasons_raw = []
        for r in matches["Reason"]:
            if r:
                all_reasons_raw.extend([x.strip() for x in r.split(";") if x.strip()])
        
        reason_series = pd.Series(all_reasons_raw).value_counts()
        
        # Crear lista con original, traducción y cuenta
        reason_list = []
        for original, count in reason_series.items():
            reason_list.append({
                "original": original,
                "translation": cls.REASONS_MAP.get(original, original),
                "count": int(count)
            })
        
        # 2. Obtener los 3 más recientes (solo para data, no los usaremos en el resumen si el user no quiere)
        matches["dt"] = pd.to_datetime(matches["RetractionDate"], errors='coerce')
        recent_matches = matches.sort_values("dt", ascending=False).head(3)
        
        examples = []
        for _, row in recent_matches.iterrows():
            nature_esp = cls.REASONS_MAP.get(row["RetractionNature"], row["RetractionNature"])
            examples.append({
                "title": row["Title"],
                "date": cls._format_date(row["RetractionDate"]),
                "reasons": cls._translate_items(row["Reason"]),
                "nature": nature_esp
            })

        summary = f"Se identificaron {total_count} registros en Retraction Watch."
        
        return {
            "count": total_count,
            "summary": summary,
            "reason_counts": reason_list,
            "examples": examples
        }
