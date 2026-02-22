import React, { useState, useEffect } from 'react';
import { RefreshCw, Database } from 'lucide-react';
import { toast } from 'sonner';

export default function AdminPage() {
    const [loadingGenerate, setLoadingGenerate] = useState(false);
    const [loadingReset, setLoadingReset] = useState(false);
    const [lastRunResult, setLastRunResult] = useState(null);

    const handleGenerateData = async () => {
        setLoadingGenerate(true);
        setLastRunResult(null);
        try {
            const resp = await fetch('http://localhost:8000/api/demo/generate-data', { method: 'POST' });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || 'Failed to generate data');

            const { transactions, invoices, match_proposals } = data.result;
            setLastRunResult(`Created ${transactions} transactions, ${invoices} invoices, ${match_proposals} match proposals`);
            toast.success('Successfully generated fresh data!');
        } catch (err) {
            toast.error(err.message);
        } finally {
            setLoadingGenerate(false);
        }
    };

    const handleResetDemo = async () => {
        if (!window.confirm("Are you sure? This will wipe the database and re-seed from scratch.")) return;

        setLoadingReset(true);
        try {
            const resp = await fetch('http://localhost:8000/api/demo/reset', { method: 'POST' });
            if (!resp.ok) throw new Error('Failed to reset data');
            toast.success('Database has been reset and re-seeded successfully.');
            setLastRunResult(null);
        } catch (err) {
            toast.error(err.message);
        } finally {
            setLoadingReset(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-12 min-h-screen bg-[var(--tt-bg)] text-[var(--tt-text)]">
            <div className="w-full max-w-2xl bg-[var(--tt-bg-alt)] border border-[var(--tt-border)] rounded-xl shadow-lg p-8">
                <h1 className="text-3xl font-bold mb-6 flex items-center gap-3">
                    <Database className="w-8 h-8 text-[var(--tt-primary)]" />
                    TunaTax Demo Admin
                </h1>

                <div className="space-y-8">
                    {/* Generate Data Section */}
                    <div className="p-6 border border-[var(--tt-border-light)] rounded-lg bg-[var(--tt-bg)]">
                        <h2 className="text-xl font-semibold mb-2">Generate Fresh Data</h2>
                        <p className="text-[var(--tt-text-muted)] mb-4">
                            This simulates new transactions arriving from Open Banking and new invoices arriving from Gmail.
                            The linking engine will attempt to match them.
                        </p>
                        <button
                            onClick={handleGenerateData}
                            disabled={loadingGenerate}
                            className="flex items-center gap-2 bg-[var(--tt-primary)] hover:bg-[var(--tt-primary-hover)] text-white px-5 py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                        >
                            {loadingGenerate ? <RefreshCw className="w-5 h-5 animate-spin" /> : <span>🐟</span>}
                            {loadingGenerate ? 'Generating Data...' : 'Generate Data'}
                        </button>

                        {lastRunResult && (
                            <p className="mt-4 text-sm text-[var(--tt-text-body)] font-medium">
                                Last run: {lastRunResult}
                            </p>
                        )}
                    </div>

                    {/* Reset Section */}
                    <div className="p-6 border border-red-900/40 rounded-lg bg-red-950/10">
                        <h2 className="text-xl font-semibold mb-2 text-red-500">Reset Demo</h2>
                        <p className="text-[var(--tt-text-muted)] mb-4">
                            Wipe all data and re-seed from scratch to the initial demo state.
                        </p>
                        <button
                            onClick={handleResetDemo}
                            disabled={loadingReset}
                            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                        >
                            <RefreshCw className={`w-5 h-5 ${loadingReset ? 'animate-spin' : ''}`} />
                            {loadingReset ? 'Resetting...' : 'Reset Everything'}
                        </button>
                    </div>

                </div>
            </div>
        </div>
    );
}
