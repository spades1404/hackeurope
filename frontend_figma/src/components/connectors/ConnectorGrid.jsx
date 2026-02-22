import { useState } from 'react';
import { ConnectorCard } from './ConnectorCard';

export const ConnectorGrid = ({ connectors: initialConnectors }) => {
  const [connectors, setConnectors] = useState(initialConnectors);

  const handleConnect = (connectorId) => {
    setConnectors(prev => 
      prev.map(c => 
        c.id === connectorId 
          ? { ...c, status: 'connected', account: 'user@example.com', last_sync: 'Just now', items_synced: 0 }
          : c
      )
    );
  };

  const handleDisconnect = (connectorId) => {
    setConnectors(prev => 
      prev.map(c => 
        c.id === connectorId 
          ? { ...c, status: 'available', account: undefined, last_sync: undefined, items_synced: undefined }
          : c
      )
    );
  };

  const connected = connectors.filter(c => c.status === 'connected');
  const available = connectors.filter(c => c.status === 'available');
  const comingSoon = connectors.filter(c => c.status === 'coming_soon');

  return (
    <div className="space-y-8">
      {/* Connected */}
      {connected.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--tt-text)' }}>
            Connected ({connected.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {connected.map(connector => (
              <ConnectorCard 
                key={connector.id} 
                connector={connector} 
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        </div>
      )}

      {/* Available */}
      {available.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--tt-text)' }}>
            Available ({available.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {available.map(connector => (
              <ConnectorCard 
                key={connector.id} 
                connector={connector} 
                onConnect={handleConnect}
              />
            ))}
          </div>
        </div>
      )}

      {/* Coming Soon */}
      {comingSoon.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--tt-text)' }}>
            Coming Soon ({comingSoon.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {comingSoon.map(connector => (
              <ConnectorCard 
                key={connector.id} 
                connector={connector}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
