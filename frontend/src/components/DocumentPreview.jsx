import React, { useRef, useEffect } from 'react';
import LiveDot from './LiveDot';

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

function todayStr() {
  const d = new Date();
  return `Lima, ${String(d.getDate()).padStart(2, '0')} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
}

export default function DocumentPreview({
  phase, form,
  meta, totalDocs, pubsByYear, pubsByCountry,
  retractedScopus, retractedWos,
  wosCollections, wosCategories, predatory,
  editables, updateEditable,
}) {
  const previewRef = useRef(null);
  const isCollecting = phase === 'collecting';
  const hasData = meta !== null;

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
              <input className="editable-field" style={{ minWidth: '250px' }} value={editables.homepage} onChange={e => updateEditable('homepage', e.target.value)} placeholder="URL del sitio web" />
            </div>
            <div className="sub-item"><span className="label">1.3 Editorial:</span> {meta.publisher}</div>
            <div className="sub-item">
              <span className="label">1.4 APC:</span>{' '}
              <input className="editable-field" value={editables.apc} onChange={e => updateEditable('apc', e.target.value)} placeholder="Monto y moneda, o 'Sin APC'" />
            </div>
            <div className="sub-item">
              <span className="label">1.5 Tiempo de publicación:</span>{' '}
              <input className="editable-field" value={editables.pub_time} onChange={e => updateEditable('pub_time', e.target.value)} placeholder="Días promedio" />
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
                {meta.scopus_link && (
                  <div style={{ marginLeft: '0.5cm', marginTop: '0.2rem' }}>
                    <a href={meta.scopus_link} target="_blank" rel="noopener noreferrer" style={{ color: '#0000FF', textDecoration: 'none', fontSize: '0.95em' }}>{meta.scopus_link}</a>
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
              {pubsByYear && Object.keys(pubsByYear).length > 0 && (
                <div className="data-grid fade-in">
                  {Object.entries(pubsByYear).sort(([a], [b]) => a - b).map(([y, c]) => (
                    <span key={y} className="data-cell"><strong>{y}:</strong> {c}</span>
                  ))}
                </div>
              )}
            </div>

            {pubsByCountry !== null && (
              <div className="fade-in">
                <h3>2.2 Documentos por país</h3>
                <div className="indent">
                  {pubsByCountry.length > 0 ? (
                    <div className="data-grid">
                      {pubsByCountry.slice(0, 10).map((p, i) => (
                        <div key={i} className="data-cell"><strong>{p.country}:</strong> {p.count.toLocaleString()}</div>
                      ))}
                    </div>
                  ) : <p style={{ color: '#999' }}>No se obtuvieron datos de países.</p>}
                </div>
              </div>
            )}

            {retractedScopus !== null && (
              <div className="fade-in">
                <h3>2.3 Artículos retractados</h3>
                <div className="indent">
                  <p>Scopus: {retractedScopus === 0 ? 'No se identificaron artículos retractados.' : `Se identificaron ${retractedScopus} artículos retractados.`}</p>
                  {retractedWos !== null && retractedWos >= 0 ? (
                    <p>WoS: {retractedWos === 0 ? 'No se identificaron artículos retractados.' : `Se identificaron ${retractedWos} artículos retractados.`}</p>
                  ) : (
                    <p>Retractados WoS: <input className="editable-field" value={editables.retracted_wos_manual} onChange={e => updateEditable('retracted_wos_manual', e.target.value)} placeholder="Número o descripción" /></p>
                  )}
                </div>
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
              {predatory.length === 0 ? (
                <p>No figura en la lista de Predatory journals ni en Beall's List.</p>
              ) : (
                <>
                  <p style={{ color: '#c00', fontWeight: 700 }}>⚠ La revista figura en listas predatorias:</p>
                  {predatory.map((h, i) => <div key={i} className="bullet" style={{ color: '#c00', fontWeight: 700 }}>{h}</div>)}
                </>
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
              {predatory.length === 0
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
