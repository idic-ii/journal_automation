import React, { useRef, useEffect } from 'react';
import LiveDot from './LiveDot';

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

function todayStr() {
  const d = new Date();
  return `Lima, ${String(d.getDate()).padStart(2, '0')} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
}

export default function DocumentPreview({
  phase, form,
  meta, totalDocs, pubsByYear, pubsByCountry, pubsByInstitution,
  retractedScopus, retractedWos,
  wosCollections, wosCategories, predatory, discontinued, retractedWatch, doaj,
  editables, updateEditable,
}) {
  const previewRef = useRef(null);
  const isCollecting = phase === 'collecting';
  const hasData = meta !== null;

  // Normalize predatory data (supports both old list format and new {hits, sources_status} format)
  const predatoryHits = Array.isArray(predatory) ? predatory : (predatory?.hits || []);
  const sourcesStatus = predatory?.sources_status || null;

  // Auto-scroll to bottom when new data arrives during collection
  useEffect(() => {
    if (isCollecting && previewRef.current) {
      const el = previewRef.current;
      setTimeout(() => {
        if (el) {
          el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        }
      }, 200);
    }
  }, [meta, totalDocs, pubsByYear, pubsByCountry, retractedScopus, retractedWos, wosCollections, wosCategories, predatory, isCollecting]);

  // ── EMPTY STATE ──
  if (!hasData && !isCollecting) {
    return (
      <main className="preview-area" ref={previewRef}>
        <div className="doc-empty">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          <p>Ingresa los datos e inicia la recolección para ver cómo el informe se completa en tiempo real</p>
        </div>
      </main>
    );
  }

  // ── LOADING STATE (waiting for first data) ──
  if (!hasData && isCollecting) {
    return (
      <main className="preview-area" ref={previewRef}>
        <div className="doc-empty">
          <div className="loading-spinner" style={{ width: 40, height: 40, borderWidth: 4 }} />
          <p>Conectando con Scopus…</p>
        </div>
      </main>
    );
  }

  // ── DOCUMENT PREVIEW ──
  return (
    <main className="preview-area" ref={previewRef}>
      <div className="doc-page">
        {/* ── ALERTA DESCONTINUADA ── */}
        {discontinued?.is_discontinued && (
          <div className="discontinued-banner fade-in">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <div>
              <strong>REVISTA DESCONTINUADA:</strong> Esta revista figura como inactiva en Scopus.
              <span style={{ marginLeft: '10px', fontSize: '0.9em', opacity: 0.9 }}>Cobertura: {discontinued.coverage}</span>
            </div>
          </div>
        )}

        {/* ── HEADER ── */}
        <div className="doc-header fade-in">
          <p>Área de Inteligencia e Integridad</p>
          <p>Instituto de Investigación Científica</p>
          <p>Universidad de Lima</p>
        </div>
        <div className="doc-report-number fade-in">
          Informe N° IDIC-IQInteg-R-{form.nro_informe || '[NÚMERO]'}
        </div>
        <div className="doc-report-title fade-in">
          Integridad científica de la revista <em>{meta.journal}</em>
        </div>
        <div className="doc-date fade-in">{todayStr()}</div>

        {/* ── ARTICLE REF ── */}
        {meta.scopus_id && (
          <div className="fade-in" style={{ marginBottom: '1.5rem' }}>
            <p style={{ fontWeight: 700, marginBottom: '0.3rem' }}>Artículo de referencia analizado</p>
            <div className="indent">
              {meta.article_title && <p><span className="label">Título:</span> {meta.article_title}</p>}
              {meta.article_author && <p><span className="label">Autor(es):</span> {meta.article_author}</p>}
              {meta.article_doi && <p><span className="label">DOI:</span> {meta.article_doi}</p>}
            </div>
          </div>
        )}

        {/* ── 1. DATOS DE LA REVISTA ── */}
        <div className="fade-in">
          <h2>1. Datos de la revista</h2>
          <div className="indent">
            <div className="sub-item"><span className="label">1.1 ISSN:</span> {meta.issn_print || '[no disponible]'};  E-ISSN: {meta.eissn}</div>
            <div className="sub-item">
              <span className="label">1.2 Sitio web:</span>{' '}
              {doaj?.journal_url ? (
                <a href={doaj.journal_url} target="_blank" rel="noopener noreferrer" className="static-field" style={{ color: '#0000FF', textDecoration: 'none' }}>
                  {doaj.journal_url}
                </a>
              ) : (
                <input className="editable-field" style={{ minWidth: '250px' }} value={editables.homepage} onChange={e => updateEditable('homepage', e.target.value)} placeholder="URL del sitio web" />
              )}
            </div>
            <div className="sub-item"><span className="label">1.3 Editorial:</span> {meta.publisher}</div>
            <div className="sub-item">
              <span className="label">1.4 APC:</span>{' '}
              {doaj?.apc ? (
                <span className="static-field">{doaj.apc}</span>
              ) : (
                <input className="editable-field" value={editables.apc} onChange={e => updateEditable('apc', e.target.value)} placeholder="Monto y moneda, o 'Sin APC'" />
              )}
            </div>
            <div className="sub-item">
              <span className="label">1.5 Tiempo de publicación:</span>{' '}
              {doaj?.pub_time_weeks ? (
                <span className="static-field">{doaj.pub_time_weeks} semanas</span>
              ) : (
                <input className="editable-field" value={editables.pub_time} onChange={e => updateEditable('pub_time', e.target.value)} placeholder="Días promedio" />
              )}
            </div>

            {/* 1.6 CiteScore */}
            {meta.quartiles && (
              <div className="fade-in">
                <div className="sub-item"><span className="label">1.6 Cuartil CiteScore (Scopus {meta.citescore_year || '2024'}):</span></div>
                {Object.entries(meta.quartiles).map(([area, items]) => (
                  <div key={area} className="indent" style={{ marginBottom: '0.5rem' }}>
                    <p>De acuerdo con el área temática <em>{area}</em>, la revista se clasifica en las siguientes categorías y cuartiles:</p>
                    {items.map((it, i) => (
                      <div key={i} className="bullet">
                        Se ubica en el cuartil {it.cuartil.replace('Q', '')} (<strong>{it.cuartil}</strong>) en la categoría <em>{it.subarea}</em>.
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {/* 1.7 WoS */}
            {(wosCollections !== null || wosCategories !== null) && (
              <div className="fade-in" style={{ marginTop: '0.5rem' }}>
                <div className="sub-item"><span className="label">1.7 Cuartil WoS (JIF {new Date().getFullYear() - 2}):</span></div>
                {(wosCategories?.length > 0 || wosCollections?.length > 0) ? (
                  <div className="indent">
                    {wosCategories?.map((cat, i) => {
                      const catName = typeof cat === 'object' ? (cat.name || '[Sin nombre]') : cat;
                      return (
                        <p key={i}>
                          Se ubica en el cuartil <input className="editable-field" style={{ width: '60px', minWidth: '60px', textAlign: 'center' }} value={editables.wos_quartiles?.[catName] || ''} onChange={e => updateEditable('wos_quartiles', { ...editables.wos_quartiles, [catName]: e.target.value })} placeholder="Q?" /> en la categoría <em>{catName}</em>.
                        </p>
                      );
                    })}
                    {wosCollections?.map((col, i) => (
                      <p key={i} style={{ marginTop: i === 0 ? '0.5rem' : 0 }}>Forma parte de la colección <em>{col}</em>.</p>
                    ))}
                    <div style={{ marginTop: '0.5rem' }}>
                      <span className="label">Colecciones manuales:</span>{' '}
                      <input className="editable-field" style={{ minWidth: '200px' }} value={editables.wos_collections_manual} onChange={e => updateEditable('wos_collections_manual', e.target.value)} placeholder="Ej: SCIE, SSCI" />
                    </div>
                  </div>
                ) : (
                  <div className="indent"><span className="editable-field" style={{ minWidth: '300px' }}>[COMPLETAR: cuartil y categoría JCR]</span></div>
                )}
              </div>
            )}

            {/* 1.8 Vigencia */}
            {meta.coverage_start && (
              <div className="sub-item fade-in" style={{ marginTop: '0.5rem' }}>
                <span className="label">1.8 Vigencia en Scopus:</span> Vigente de {meta.coverage_start} a {meta.coverage_end}.
                {discontinued?.is_discontinued && (
                  <span style={{ color: '#c00', fontWeight: 700, marginLeft: '0.4rem' }}>
                    (cobertura descontinuada en Scopus)
                  </span>
                )}
                {discontinued?.is_discontinued && (
                  <div style={{ color: '#c00', fontWeight: 700, marginTop: '0.2rem' }}>
                    ⚠ REVISTA DESCONTINUADA (Cobertura: {discontinued.coverage})
                  </div>
                )}

                {/* 1.9 Tendencia de Impacto */}
                <div style={{ marginTop: '1.2rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                  <span className="label" style={{ color: '#800000' }}>1.9 Tendencia de impacto (CiteScore):</span>
                  {meta.citescore_history && meta.citescore_history.length >= 2 ? (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
                      <svg width="100%" height="150" viewBox="0 0 500 150" preserveAspectRatio="none">
                        {/* Grid lines */}
                        {[0, 37, 75, 112, 150].map(y => (
                          <line key={y} x1="0" y1={y} x2="500" y2={y} stroke="#eee" strokeWidth="1" />
                        ))}
                        {/* Trend Line with Padding */}
                        <polyline
                          fill="none"
                          stroke="#800000"
                          strokeWidth="2"
                          points={meta.citescore_history.map((h, i) => {
                            const maxScore = Math.max(...meta.citescore_history.map(x => x.score), 0.1);
                            // Padding of 30px on each side
                            const x = 30 + (i / (meta.citescore_history.length - 1)) * 440;
                            const y = 130 - (h.score / maxScore) * 110;
                            return `${x},${y}`;
                          }).join(' ')}
                        />
                        {/* Data Points */}
                        {meta.citescore_history.map((h, i) => {
                          const maxScore = Math.max(...meta.citescore_history.map(x => x.score), 0.1);
                          const x = 30 + (i / (meta.citescore_history.length - 1)) * 440;
                          const y = 130 - (h.score / maxScore) * 110;
                          return (
                            <g key={i}>
                              <rect x={x-3} y={y-3} width="6" height="6" fill="#fff" stroke="#800000" strokeWidth="1.5" />
                              <text x={x} y={y-12} textAnchor="middle" fontSize="10" fontWeight="bold" fill="#800000">{h.score.toFixed(2)}</text>
                              <text x={x} y="145" textAnchor="middle" fontSize="9" fill="#666">{h.year}</text>
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  ) : (
                    <div style={{ marginTop: '0.8rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px', border: '1px dashed #ccc', color: '#666', fontStyle: 'italic', fontSize: '0.85rem' }}>
                      {meta.citescore_history ? "Datos históricos insuficientes para generar tendencia." : "Cargando historial de impacto..."}
                    </div>
                  )}
                </div>
                {meta.scopus_link && (
                  <div style={{ marginLeft: '0.5cm', marginTop: '0.2rem' }}>
                    <a href={meta.scopus_link} target="_blank" rel="noopener noreferrer" style={{ color: '#0000FF', textDecoration: 'none', fontSize: '0.95em' }}>{meta.scopus_link}</a>
                  </div>
                )}
              </div>
            )}

            {/* OA Type (from Scopus metadata) */}
            {meta.open_access != null && (
              <div className="sub-item fade-in" style={{ marginTop: '0.5rem' }}>
                <span className="label">Acceso Abierto:</span>{' '}
                {meta.open_access
                  ? <span style={{ color: '#2e7d32', fontWeight: 600 }}>Sí{meta.oa_type ? ` (${meta.oa_type})` : ''}</span>
                  : <span>No es Open Access</span>
                }
              </div>
            )}

            {/* DOAJ Verification Panel */}
            {doaj && (
              <div className="fade-in" style={{
                marginTop: '1rem',
                padding: '1.25rem',
                borderRadius: '4px',
                background: doaj.in_doaj ? '#f8fafc' : '#fff1f2',
                borderLeft: `4px solid ${doaj.in_doaj ? '#0f172a' : '#be123c'}`,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                fontFamily: 'inherit'
              }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '1rem', borderBottom: '1px solid rgba(0,0,0,0.05)', paddingBottom: '0.5rem' }}>
                  <h3 style={{
                    margin: 0,
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: doaj.in_doaj ? '#0f172a' : '#be123c'
                  }}>
                    {doaj.in_doaj ? 'Verificación DOAJ: Registrada' : 'Verificación DOAJ: No Registrada'}
                  </h3>
                </div>

                {doaj.in_doaj && (
                  <>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.85rem' }}>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>APC:</span> {doaj.apc || 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Tiempo de pub.:</span> {doaj.pub_time_weeks ? `${doaj.pub_time_weeks} semanas` : 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Proceso de revisión:</span> {doaj.review_process?.length > 0 ? doaj.review_process.join(', ') : 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Licencias:</span> {doaj.licenses?.length > 0 ? doaj.licenses.join(', ') : 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Preservación:</span> {doaj.preservation?.length > 0 ? doaj.preservation.join(', ') : 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Detección de plagio:</span> {doaj.plagiarism_detection ? 'Implementado' : 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Inicio OA:</span> {doaj.oa_start || 'No declarado'}
                      </div>
                      <div className="sub-info-item">
                        <span style={{ fontWeight: 600, color: '#475569' }}>Conformidad BOAI:</span> {doaj.boai_compliant ? 'Sí' : 'No declarado'}
                      </div>
                      {doaj.last_review && (
                        <div className="sub-info-item" style={{ gridColumn: 'span 2', marginTop: '0.5rem', borderTop: '1px dashed #e2e8f0', paddingTop: '0.5rem' }}>
                          <span style={{ fontWeight: 600, color: '#475569' }}>Última revisión completa por DOAJ:</span> {doaj.last_review}
                        </div>
                      )}
                    </div>

                    {/* Glossary / Legend */}
                    <div style={{ 
                      marginTop: '1.25rem', 
                      paddingTop: '1rem', 
                      borderTop: '1px solid rgba(0,0,0,0.05)', 
                      fontSize: '0.72rem', 
                      color: '#64748b',
                      lineHeight: '1.4'
                    }}>
                      <div style={{ fontWeight: 600, marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.02em', fontSize: '0.65rem' }}>Glosario de términos DOAJ</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem 1rem' }}>
                        <div><strong style={{color:'#475569'}}>APC:</strong> Costo cobrado a los autores para publicar en Acceso Abierto.</div>
                        <div><strong style={{color:'#475569'}}>Revisión:</strong> Método de evaluación científica (ej: doble ciego).</div>
                        <div><strong style={{color:'#475569'}}>Preservación:</strong> Archivo digital a largo plazo (ej: Portico, CLOCKSS).</div>
                        <div><strong style={{color:'#475569'}}>BOAI:</strong> Cumple con la Iniciativa de Budapest para el Acceso Abierto.</div>
                        <div><strong style={{color:'#475569'}}>Sello DOAJ:</strong> Otorgado a revistas con estándares éticos excepcionales.</div>
                        <div><strong style={{color:'#475569'}}>Plagio:</strong> Uso de herramientas (iThenticate/Crossref) para validar originalidad.</div>
                      </div>
                    </div>
                  </>
                )}

                {!doaj.in_doaj && (
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#991b1b' }}>
                    La revista no figura en el Directory of Open Access Journals (DOAJ). Se recomienda verificar manualmente si el acceso abierto es gestionado bajo otros estándares institucionales.
                  </p>
                )}

                {doaj.status === 'error' && doaj.message && (
                  <div style={{ color: '#be123c', fontSize: '0.8rem', marginTop: '0.75rem', padding: '0.5rem', background: 'rgba(190, 18, 60, 0.05)', borderLeft: '2px solid #be123c' }}>
                    Error de consulta: {doaj.message}
                  </div>
                )}
              </div>
            )}
          </div>

          {isCollecting && totalDocs === null && (
            <div className="section-loading"><div className="loading-spinner small" /><span>Cargando producción científica…</span></div>
          )}
        </div>

        {/* ── 2. PRODUCCIÓN CIENTÍFICA ── */}
        {totalDocs !== null && (
          <div className="fade-in">
            <h2>2. Producción científica de la revista</h2>
            <h3>2.1 Publicaciones por año</h3>
            <div className="indent">
              <p>La revista registra {totalDocs.toLocaleString()} documentos indexados en Scopus.</p>
              {pubsByYear && Object.keys(pubsByYear).length > 0 ? (
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
                  <svg width="100%" height="150" viewBox="0 0 500 150" preserveAspectRatio="none">
                    <polyline
                      fill="none"
                      stroke="#1F4E78"
                      strokeWidth="1.5"
                      points={Object.entries(pubsByYear).sort(([a], [b]) => a - b).map(([y, c], i, arr) => {
                        const maxVal = Math.max(...Object.values(pubsByYear).map(Number), 1);
                        const x = 30 + (i / (arr.length - 1)) * 440;
                        const yVal = 130 - (Number(c) / maxVal) * 110;
                        return `${x},${yVal}`;
                      }).join(' ')}
                    />
                    {Object.entries(pubsByYear).sort(([a], [b]) => a - b).map(([y, c], i, arr) => {
                      const maxVal = Math.max(...Object.values(pubsByYear).map(Number), 1);
                      const x = 30 + (i / (arr.length - 1)) * 440;
                      const yVal = 130 - (Number(c) / maxVal) * 110;
                      return (
                        <g key={y}>
                          <circle cx={x} cy={yVal} r="3.5" fill="#fff" stroke="#1F4E78" strokeWidth="1.5" />
                          <text x={x} y={yVal-10} textAnchor="middle" fontSize="9" fontWeight="bold" fill="#1F4E78">{c.toLocaleString()}</text>
                          <text x={x} y="145" textAnchor="middle" fontSize="8" fill="#666">{y}</text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              ) : (
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px', border: '1px dashed #ccc', color: '#666' }}>
                  Cargando desglose por año...
                </div>
              )}
            </div>

            {pubsByCountry !== null && (
              <div className="fade-in">
                <h3>2.2 Documentos por país</h3>
                <div className="indent">
                  {pubsByCountry && pubsByCountry.length > 0 ? (
                    <div style={{ marginTop: '1rem', padding: '1.5rem', background: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {pubsByCountry.slice(0, 10).map((p, i) => {
                          const maxVal = Math.max(...pubsByCountry.map(x => x.count), 1);
                          const width = (p.count / maxVal) * 75;
                          return (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{ 
                                width: '120px', 
                                fontSize: '0.75rem', 
                                textAlign: 'right', 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                whiteSpace: 'nowrap',
                                color: '#44546A',
                                fontWeight: 'bold'
                              }} title={p.country}>
                                {p.country}
                              </div>
                              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ 
                                  width: `${width}%`, 
                                  height: '16px', 
                                  backgroundColor: '#44546A', 
                                  borderRadius: '0 2px 2px 0' 
                                }} />
                                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#44546A' }}>
                                  {p.count.toLocaleString('en-US')}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px', border: '1px dashed #ccc', color: '#666' }}>
                      Cargando distribución geográfica...
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 2.3 Documentos por institución */}
            {pubsByInstitution && (
              <div className="fade-in" style={{ marginTop: '1.5rem' }}>
                <h3>2.3 Documentos por institución</h3>
                <div className="indent">
                  {pubsByInstitution.length > 0 ? (
                    <div style={{ marginTop: '1rem', padding: '1.5rem', background: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {pubsByInstitution.slice(0, 10).map((p, i) => {
                          const maxVal = Math.max(...pubsByInstitution.map(x => x.count), 1);
                          const width = (p.count / maxVal) * 75; // Leave space for label
                          return (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{ 
                                width: '160px', 
                                fontSize: '0.75rem', 
                                textAlign: 'right', 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                whiteSpace: 'nowrap',
                                color: '#44546A',
                                fontWeight: 'bold'
                              }} title={p.institution}>
                                {p.institution}
                              </div>
                              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ 
                                  width: `${width}%`, 
                                  height: '16px', 
                                  backgroundColor: '#1F4E78', 
                                  borderRadius: '0 2px 2px 0' 
                                }} />
                                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#1F4E78' }}>
                                  {p.count.toLocaleString('en-US')}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px', border: '1px dashed #ccc', color: '#666' }}>
                      Cargando distribución institucional...
                    </div>
                  )}
                </div>
              </div>
            )}

            {retractedScopus !== null && (
              <div className="fade-in">
                <h3>2.4 Artículos retractados por la revista</h3>
                <div className="indent">
                  <ul>
                    <li>
                      <strong>Scopus:</strong> {retractedScopus === 0 ? 'No se identificaron artículos retractados.' : 
                        retractedScopus === 1 ? 'Se identificó 1 artículo retractado.' : 
                        `Se identificaron ${retractedScopus} artículos retractados.`}
                    </li>
                    {retractedWos !== null && (
                      <li>
                        <strong>Web of Science:</strong> {retractedWos === 0 ? 'No se identificaron artículos retractados.' : 
                          retractedWos === 1 ? 'Se identificó 1 artículo retractado.' : 
                          `Se identificaron ${retractedWos} artículos retractados.`}
                      </li>
                    )}
                  </ul>
                </div>

                {retractedWatch && (
                  <div style={{ marginTop: '1rem', marginLeft: '2rem', padding: '15px', backgroundColor: '#fff4f4', borderLeft: '5px solid #c00000', borderRadius: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                    <h4 style={{ color: '#c00000', margin: '0 0 8px 0', fontSize: '1.1rem' }}>2.5 Análisis Retraction Watch</h4>
                    <p style={{ marginBottom: '12px' }}><strong>{retractedWatch.summary}</strong></p>

                    {/* Breakdown by reasons with Custom Tooltip */}
                    {retractedWatch.reason_counts && retractedWatch.reason_counts.length > 0 && (
                      <div style={{ marginBottom: '1.25rem' }}>
                        <p style={{ fontSize: '0.85rem', fontWeight: 600, color: '#666', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                          Frecuencia por motivo:
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {retractedWatch.reason_counts.map((rc, i) => (
                            <div 
                              key={i} 
                              className="retraction-badge-container"
                              style={{ position: 'relative' }}
                            >
                              <div 
                                className="retraction-badge"
                                style={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  backgroundColor: 'white', 
                                  border: '1px solid #ffcdd2', 
                                  borderRadius: '6px', 
                                  overflow: 'hidden',
                                  fontSize: '0.82rem',
                                  cursor: 'help',
                                  transition: 'all 0.2s ease',
                                  boxShadow: '0 2px 4px rgba(192, 0, 0, 0.05)'
                                }}
                              >
                                <span style={{ padding: '5px 12px', color: '#444', fontWeight: 500 }}>{rc.original}</span>
                                <span style={{ 
                                  backgroundColor: '#c00000', 
                                  color: 'white', 
                                  padding: '5px 10px', 
                                  fontWeight: 700,
                                  minWidth: '28px',
                                  textAlign: 'center'
                                }}>{rc.count}</span>
                              </div>
                              
                              {/* Custom Tooltip */}
                              <div className="retraction-tooltip">
                                <div style={{ fontWeight: 700, marginBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '4px' }}>
                                  {rc.original}
                                </div>
                                {rc.translation}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {isCollecting && predatory === null && (
              <div className="section-loading"><div className="loading-spinner small" /><span>Verificando listas predatorias…</span></div>
            )}
          </div>
        )}

        {/* ── 3. LISTAS PREDATORIAS ── */}
        {predatory !== null && (
          <div className="fade-in">
            <h2>3. Verificación de listas de revistas predatorias</h2>
            <div className="indent">
              {predatoryHits.length === 0 ? (
                <p>No figura en la lista de Predatory journals ni en Beall's List.</p>
              ) : (
                <>
                  <p style={{ color: '#c00', fontWeight: 700 }}>⚠ La revista figura en listas predatorias:</p>
                  {predatoryHits.map((h, i) => <div key={i} className="bullet" style={{ color: '#c00', fontWeight: 700 }}>{h}</div>)}
                </>
              )}

              {/* Source verification status */}
              {sourcesStatus && (
                <div style={{
                  marginTop: '1rem', padding: '12px', borderRadius: '6px',
                  background: '#f5f5f5', border: '1px solid #e0e0e0', fontSize: '0.85rem'
                }}>
                  <div style={{ fontWeight: 600, marginBottom: '6px', color: '#555' }}>Estado de fuentes verificadas:</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                    {Object.entries(sourcesStatus).map(([src, status]) => (
                      <div key={src} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ color: status === 'ok' ? '#2e7d32' : '#c62828' }}>
                          {status === 'ok' ? '✓' : '✗'}
                        </span>
                        <span style={{ color: status === 'ok' ? '#333' : '#c62828' }}>
                          {src.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── 4. CONCLUSIONES ── */}
        {predatory !== null && (
          <div className="fade-in">
            <h2>4. Conclusiones</h2>
            <div className="sub-item"><span className="label">4.1</span> Es una revista indexada en la base de datos Scopus (vigente de {meta.coverage_start} a {meta.coverage_end}).</div>
            <div className="sub-item"><span className="label">4.2</span>{' '}
              {meta.quartiles && Object.keys(meta.quartiles).length > 0
                ? `Presenta métricas CiteScore con clasificación en ${Object.values(meta.quartiles).flat().map(i => i.cuartil).sort()[0] || 'N/A'} en sus categorías de mayor desempeño.`
                : <input className="editable-field" style={{ width: '100%' }} value={editables.concl_metrics} onChange={e => updateEditable('concl_metrics', e.target.value)} placeholder="Describir desempeño en métricas" />
              }
            </div>
            <div className="sub-item"><span className="label">4.3</span>{' '}
              {predatoryHits.length === 0
                ? 'No presenta indicios de malas prácticas (no figura en listas predatorias).'
                : <span style={{ color: '#c00' }}>Figura en listas de revistas predatorias. Se recomienda evaluar con cautela.</span>
              }
            </div>
          </div>
        )}

        {/* ── 5. RECOMENDACIONES ── */}
        {predatory !== null && (
          <div className="fade-in">
            <h2>5. Recomendaciones</h2>
            <div className="sub-item"><span className="label">5.1</span> Para elecciones futuras de una revista científica, se recomienda leer el Protocolo para la evaluación de la idoneidad de publicaciones científicas.</div>
            <div className="sub-item"><span className="label">5.2</span> Es importante reconocer que el comportamiento editorial, la calidad y la reputación de una revista pueden cambiar con el tiempo. Se aconseja verificar sus indexaciones periódicamente.</div>
          </div>
        )}

        <LiveDot visible={isCollecting} />
      </div>
    </main>
  );
}
