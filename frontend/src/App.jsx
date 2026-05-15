import React from 'react';
import useStreamCollect from './hooks/useStreamCollect';
import Sidebar from './components/Sidebar';
import DocumentPreview from './components/DocumentPreview';
import './index.css';

export default function App() {
  const {
    form, handleFormChange,
    editables, updateEditable,
    phase, startCollect, stopCollect, generateDocx,
    meta, totalDocs, pubsByYear, pubsByCountry, pubsByInstitution,
    retractedScopus, retractedWos,
    wosCollections, wosCategories,
    predatory,
    discontinued,
    retractedWatch,
    doaj,
    reportId, error, logs,
  } = useStreamCollect();

  return (
    <div className="app">
      <Sidebar
        form={form}
        handleFormChange={handleFormChange}
        phase={phase}
        startCollect={startCollect}
        stopCollect={stopCollect}
        generateDocx={generateDocx}
        reportId={reportId}
        error={error}
        logs={logs}
      />
      <DocumentPreview
        phase={phase}
        form={form}
        meta={meta}
        totalDocs={totalDocs}
        pubsByYear={pubsByYear}
        pubsByCountry={pubsByCountry}
        pubsByInstitution={pubsByInstitution}
        retractedScopus={retractedScopus}
        retractedWos={retractedWos}
        wosCollections={wosCollections}
        wosCategories={wosCategories}
        predatory={predatory}
        discontinued={discontinued}
        retractedWatch={retractedWatch}
        doaj={doaj}
        editables={editables}
        updateEditable={updateEditable}
      />
    </div>
  );
}
