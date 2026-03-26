import { useState, useCallback, useRef } from 'react';
import { flushSync } from 'react-dom';

const API_HTTP = 'http://localhost:8000';
const API_WS   = 'ws://localhost:8000';

/**
 * Custom hook: manages data collection via WebSocket and DOCX generation via HTTP.
 * WebSocket guarantees each event is delivered as a discrete message — no buffering issues.
 */
export default function useStreamCollect() {
  // ── Form ──
  const [form, setForm] = useState({ api_key: '', scopus_id: '', eissn: '', nro_informe: '', wos_api_key: '' });

  // ── Workflow ──
  const [phase, setPhase] = useState('input'); // input | collecting | review | generating | done

  // ── Logs ──
  const [logs, setLogs] = useState([]);

  // ── Data slices ──
  const [meta, setMeta] = useState(null);
  const [totalDocs, setTotalDocs] = useState(null);
  const [pubsByYear, setPubsByYear] = useState(null);
  const [pubsByCountry, setPubsByCountry] = useState(null);
  const [retractedScopus, setRetractedScopus] = useState(null);
  const [retractedWos, setRetractedWos] = useState(null);
  const [wosCollections, setWosCollections] = useState(null);
  const [wosCategories, setWosCategories] = useState(null);
  const [predatory, setPredatory] = useState(null);

  // ── Full bundle (received at end) ──
  const fullTaskData = useRef(null);

  // ── Editables ──
  const [editables, setEditables] = useState({ apc: '', pub_time: '', retracted_wos_manual: '' });

  // ── Output ──
  const [reportId, setReportId] = useState(null);
  const [error, setError] = useState(null);

  // ── Helpers ──
  const addLog = useCallback((content, type = 'info') => {
    setLogs(prev => [...prev, { id: Date.now() + Math.random(), content, type }]);
  }, []);

  const handleFormChange = useCallback((e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  }, []);

  const updateEditable = useCallback((field, value) => {
    setEditables(prev => ({ ...prev, [field]: value }));
  }, []);

  const resetData = useCallback(() => {
    setMeta(null); setTotalDocs(null); setPubsByYear(null); setPubsByCountry(null);
    setRetractedScopus(null); setRetractedWos(null); setWosCollections(null);
    setWosCategories(null); setPredatory(null); fullTaskData.current = null;
  }, []);

  // ── Process a single WS event ──
  const processEvent = useCallback((ev) => {
    if (ev.type === 'step') {
      flushSync(() => addLog(ev.content, 'step'));
    }
    else if (ev.type === 'data') {
      const data = ev.content;
      const key = data._key;
      flushSync(() => {
        if (key === 'meta')              { setMeta(data); addLog(`Revista: ${data.journal}`, 'info'); }
        else if (key === 'total_docs')   { setTotalDocs(data.value); }
        else if (key === 'pubs_by_year') { setPubsByYear(data.value); }
        else if (key === 'pubs_by_country') { setPubsByCountry(data.value); }
        else if (key === 'retracted_scopus') { setRetractedScopus(data.value); }
        else if (key === 'retracted_wos')    { setRetractedWos(data.value); }
        else if (key === 'wos_collections')  { setWosCollections(data.value); }
        else if (key === 'wos_categories')   { setWosCategories(data.value); }
        else if (key === 'predatory')        { setPredatory(data.value); }
      });
    }
    else if (ev.type === 'collect_done') {
      fullTaskData.current = ev.content;
    }
    else if (ev.type === 'info')  { addLog(ev.content, 'info'); }
    else if (ev.type === 'warn')  { addLog(ev.content, 'warn'); }
    else if (ev.type === 'error') {
      flushSync(() => { addLog(ev.content, 'error'); setError(ev.content); setPhase('input'); });
    }
    else if (ev.type === 'done') {
      flushSync(() => {
        setPhase('review');
        addLog('Recolección completada. Revisa los datos.', 'step');
      });
    }
  }, [addLog]);

  // ═════════════════════════════════════════════════════════════════════
  //  Phase 1: Collect via WebSocket
  // ═════════════════════════════════════════════════════════════════════
  const startCollect = useCallback((e) => {
    e.preventDefault();
    flushSync(() => {
      setPhase('collecting');
      setLogs([]);
      setError(null);
    });
    resetData();
    addLog('Conectando con el servidor…', 'step');

    const ws = new WebSocket(`${API_WS}/ws/collect`);

    ws.onopen = () => {
      console.log('[WS] Connected');
      addLog('Iniciando recolección de datos…', 'step');
      // Send params
      ws.send(JSON.stringify({
        api_key: form.api_key,
        scopus_id: form.scopus_id,
        eissn: form.eissn,
        wos_api_key: form.wos_api_key,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const ev = JSON.parse(event.data);
        processEvent(ev);
      } catch (err) {
        console.warn('[WS] Parse error:', err, event.data);
      }
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
      flushSync(() => {
        addLog('Error de conexión con el servidor.', 'error');
        setError('Error de conexión WebSocket.');
        setPhase('input');
      });
    };

    ws.onclose = (event) => {
      console.log('[WS] Closed:', event.code, event.reason);
      // If still in collecting phase (abnormal close), set to review if we have data
      setPhase(prev => {
        if (prev === 'collecting') {
          addLog('Conexión cerrada.', 'info');
          return fullTaskData.current ? 'review' : 'input';
        }
        return prev;
      });
    };
  }, [form, addLog, resetData, processEvent]);

  // ═════════════════════════════════════════════════════════════════════
  //  Phase 2: Generate DOCX via HTTP POST
  // ═════════════════════════════════════════════════════════════════════
  const generateDocx = useCallback(async () => {
    setPhase('generating');
    addLog('Generando documento Word…', 'step');

    try {
      const reportData = fullTaskData.current
        ? { ...fullTaskData.current }
        : { meta, total_docs: totalDocs, pubs_by_year: pubsByYear, pubs_by_country: pubsByCountry,
            retracted_scopus: retractedScopus, retracted_wos: retractedWos,
            wos_collections: wosCollections, wos_categories: wosCategories, predatory };

      reportData.apc = editables.apc;
      reportData.pub_time = editables.pub_time;
      reportData.retracted_wos_manual = editables.retracted_wos_manual;

      const payload = {
        api_key: form.api_key,
        report_data: reportData,
        nro_informe: form.nro_informe || '[COMPLETAR]',
        institucion: ['Área de Inteligencia e Integridad', 'Instituto de Investigación Científica', 'Universidad de Lima'],
      };

      const resp = await fetch(`${API_HTTP}/generate-docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();

      if (resp.ok) {
        setReportId(data.report_id);
        setPhase('done');
        addLog('Documento generado con éxito.', 'step');
      } else {
        addLog(data.detail || 'Error al generar.', 'error');
        setPhase('review');
      }
    } catch (err) {
      addLog('Error de conexión.', 'error');
      setPhase('review');
    }
  }, [form, editables, meta, totalDocs, pubsByYear, pubsByCountry, retractedScopus, retractedWos, wosCollections, wosCategories, predatory, addLog]);

  return {
    form, handleFormChange,
    editables, updateEditable,
    phase, startCollect, generateDocx,
    meta, totalDocs, pubsByYear, pubsByCountry,
    retractedScopus, retractedWos,
    wosCollections, wosCategories,
    predatory,
    reportId, error, logs,
  };
}
