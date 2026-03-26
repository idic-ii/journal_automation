import React, { useRef, useEffect } from 'react';

export default function Sidebar({
  form, handleFormChange, phase,
  startCollect, generateDocx,
  reportId, error, logs,
}) {
  const timelineRef = useRef(null);
  useEffect(() => { timelineRef.current?.scrollTo(0, 99999); }, [logs]);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <div>
          <h1>Generador de Reporte</h1>
          <span>IDIC — Universidad de Lima</span>
        </div>
      </div>

      <div className="sidebar-content">
        {/* ── Form ── */}
        <form onSubmit={startCollect} className="config-group">
          <div className="group-title">Credenciales</div>
          <div className="input-block">
            <div className="input-group">
              <label>Scopus API Key</label>
              <input type="password" name="api_key" value={form.api_key} onChange={handleFormChange} required placeholder="Paste your API key" />
            </div>
            <div className="input-group">
              <label>WoS API Key (Starter)</label>
              <input type="password" name="wos_api_key" value={form.wos_api_key} onChange={handleFormChange} placeholder="Opcional" />
            </div>
          </div>

          <div className="group-title">Identificadores</div>
          <div className="input-block">
            <div className="input-row">
              <div className="input-group">
                <label>Scopus ID</label>
                <input type="text" name="scopus_id" value={form.scopus_id} onChange={handleFormChange} placeholder="2-s2.0-..." />
              </div>
              <div className="input-group">
                <label>E-ISSN</label>
                <input type="text" name="eissn" value={form.eissn} onChange={handleFormChange} placeholder="XXXX-XXXX" />
              </div>
            </div>
          </div>

          <div className="group-title">Exportación</div>
          <div className="input-block">
            <div className="input-group">
              <label>Número de Informe</label>
              <input type="text" name="nro_informe" value={form.nro_informe} onChange={handleFormChange} placeholder="Ej: 036-2026" />
            </div>
          </div>

          <button type="submit" className="btn-collect" disabled={phase === 'collecting' || phase === 'generating'}>
            {phase === 'collecting' ? <><div className="loading-spinner" /> Recolectando…</> : 'Iniciar Recolección'}
          </button>
        </form>

        {/* ── Action Buttons ── */}
        {phase === 'review' && (
          <button onClick={generateDocx} className="btn-generate-final">
            Generar Documento Final (.docx)
          </button>
        )}
        {phase === 'generating' && (
          <button className="btn-generate-final" disabled>
            <div className="loading-spinner" /> Generando…
          </button>
        )}
        {reportId && phase === 'done' && (
          <div className="status-bar success">
            <p>¡Informe generado con éxito!</p>
            <a href={`http://localhost:8000/download-docx/${reportId}`} className="download-link">⬇ Descargar informe.docx</a>
          </div>
        )}
        {error && <div className="status-bar error">{error}</div>}

        {/* ── Timeline ── */}
        <div className="timeline-container">
          <div className="group-title">Progreso</div>
          <div className="timeline" ref={timelineRef}>
            {logs.map(log => (
              <div key={log.id} className={`timeline-item ${log.type}`}>
                <div className="timeline-dot" />
                <div className="timeline-content">{log.content}</div>
              </div>
            ))}
            {logs.length === 0 && (
              <div style={{ color: '#555', fontSize: '0.8rem', textAlign: 'center', padding: '1rem' }}>
                Sin actividad
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
