import { useState } from 'react';
import { AppShell } from '../components/layout/AppShell';
import { ComplianceOverview } from '../components/compliance/ComplianceOverview';
import { DocumentDetailPanel } from '../components/compliance/DocumentDetailPanel';
import { MOCK_COMPLIANCE_DOCS } from '../data/mockData';

export const CompliancePage = () => {
  const [selectedDoc, setSelectedDoc] = useState(null);

  return (
    <AppShell title="Compliance">
      <ComplianceOverview 
        documents={MOCK_COMPLIANCE_DOCS}
        onDocumentClick={setSelectedDoc}
      />
      
      <DocumentDetailPanel
        document={selectedDoc}
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />
    </AppShell>
  );
};
