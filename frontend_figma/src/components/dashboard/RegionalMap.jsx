import { motion } from 'motion/react';

export const RegionalMap = ({ financials, complianceDocs }) => {
  const regions = [
    { code: 'US', name: 'United States', flag: '🇺🇸', x: 120, y: 100 },
    { code: 'UK', name: 'United Kingdom', flag: '🇬🇧', x: 280, y: 80 },
    { code: 'DE', name: 'Germany', flag: '🇩🇪', x: 300, y: 90 },
    { code: 'AU', name: 'Australia', flag: '🇦🇺', x: 450, y: 180 },
  ];

  const getUnresolvedCount = (code) => {
    return complianceDocs.filter(doc => 
      doc.jurisdiction === code && (doc.status === 'overdue' || doc.status === 'upcoming')
    ).length;
  };

  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        Regional Activity
      </h3>

      <div className="relative h-64">
        <svg width="100%" height="100%" viewBox="0 0 600 250">
          {/* Connection lines */}
          <g opacity="0.1">
            <line x1="280" y1="80" x2="300" y2="90" stroke="var(--tt-primary)" strokeWidth="2" />
            <line x1="120" y1="100" x2="280" y2="80" stroke="var(--tt-primary)" strokeWidth="2" strokeDasharray="5,5" />
          </g>

          {/* Region nodes */}
          {regions.map((region, index) => {
            const hasUnresolved = getUnresolvedCount(region.code) > 0;
            const data = financials.by_jurisdiction[region.code];
            
            return (
              <g key={region.code}>
                {/* Pulsing indicator for unresolved items */}
                {hasUnresolved && (
                  <motion.circle
                    cx={region.x}
                    cy={region.y}
                    r="30"
                    fill="var(--tt-warning)"
                    opacity="0.2"
                    animate={{ r: [25, 35, 25], opacity: [0.1, 0.3, 0.1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}

                {/* Main circle */}
                <motion.circle
                  cx={region.x}
                  cy={region.y}
                  r="25"
                  fill="var(--tt-primary-ghost)"
                  stroke="var(--tt-primary)"
                  strokeWidth="2"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1, type: 'spring' }}
                  className="cursor-pointer hover:opacity-80"
                />

                {/* Flag emoji */}
                <text
                  x={region.x}
                  y={region.y + 5}
                  textAnchor="middle"
                  fontSize="24"
                  className="pointer-events-none"
                >
                  {region.flag}
                </text>

                {/* Region code */}
                <text
                  x={region.x}
                  y={region.y + 45}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="600"
                  fill="var(--tt-text-body)"
                >
                  {region.code}
                </text>

                {/* Tax exposure */}
                {data && (
                  <text
                    x={region.x}
                    y={region.y + 60}
                    textAnchor="middle"
                    fontSize="10"
                    fill="var(--tt-text-muted)"
                    fontFamily="var(--font-mono)"
                  >
                    {data.currency === 'USD' && '$'}
                    {data.currency === 'GBP' && '£'}
                    {data.currency === 'EUR' && '€'}
                    {data.currency === 'AUD' && 'A$'}
                    {(data.tax_exposure / 1000).toFixed(0)}K
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="mt-4 flex items-center gap-4 text-sm" style={{ color: 'var(--tt-text-muted)' }}>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[var(--tt-primary)]"></div>
          <span>Active jurisdiction</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[var(--tt-warning)] animate-pulse"></div>
          <span>Pending items</span>
        </div>
      </div>
    </div>
  );
};
