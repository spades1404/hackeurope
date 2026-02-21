import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider, useAppContext } from './contexts/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { PageWrapper } from './components/layout/PageWrapper';
import { WorkerDashboard } from './components/worker/WorkerDashboard';
import { BusinessDashboard } from './components/business/BusinessDashboard';
import { ComplianceTab as WorkerCompliance } from './components/worker/ComplianceTab';
import { ConnectorsTab } from './components/shared/ConnectorsTab';
import { ChatPanel } from './components/shared/ChatPanel';
import { ComplianceStatus } from './components/business/ComplianceStatus';

// A simple wrapper for Business Compliance Tab since it's read-only
const BusinessCompliance = () => (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px' }}>Compliance Overview</h1>
        <ComplianceStatus />
    </div>
);

const AppContent = () => {
    const { role } = useAppContext();
    const [chatOpen, setChatOpen] = useState(false);

    return (
        <BrowserRouter>
            <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--color-bg-base)' }}>
                <Sidebar onOpenChat={() => setChatOpen(true)} />

                <div style={{ flex: 1, marginLeft: '240px', display: 'flex', flexDirection: 'column' }}>
                    <TopBar />

                    <main style={{ flex: 1, backgroundColor: 'var(--color-bg-base)' }}>
                        <PageWrapper>
                            <Routes>
                                <Route path="/" element={role === 'worker' ? <WorkerDashboard /> : <BusinessDashboard />} />
                                <Route path="/compliance" element={role === 'worker' ? <WorkerCompliance /> : <BusinessCompliance />} />
                                <Route path="/connectors" element={<ConnectorsTab />} />
                            </Routes>
                        </PageWrapper>
                    </main>
                </div>

                <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
            </div>
        </BrowserRouter>
    );
};

function App() {
    return (
        <AppProvider>
            <AppContent />
        </AppProvider>
    );
}

export default App;
