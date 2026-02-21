import React, { useState } from 'react';

export const Tabs = ({ tabs }) => {
    const [selectedIndex, setSelectedIndex] = useState(0);

    return (
        <div style={{ width: '100%' }}>
            <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--color-bg-base)', padding: '4px', borderRadius: '10px', border: '1px solid var(--color-border)' }}>
                {tabs.map((tab, idx) => {
                    const isSelected = selectedIndex === idx;
                    return (
                        <button
                            key={tab.name}
                            onClick={() => setSelectedIndex(idx)}
                            style={{
                                flex: 1,
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontSize: '14px',
                                fontWeight: '500',
                                color: isSelected ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                                backgroundColor: isSelected ? 'var(--color-bg-surface)' : 'transparent',
                                border: isSelected ? '1px solid var(--color-border)' : '1px solid transparent',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                            }}
                        >
                            {tab.name}
                        </button>
                    );
                })}
            </div>
            <div style={{ marginTop: '16px' }}>
                {tabs[selectedIndex]?.content}
            </div>
        </div>
    );
};
