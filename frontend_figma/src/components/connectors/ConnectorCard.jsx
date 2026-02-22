import { useState } from 'react';
import { RefreshCw, Settings, X, Plus } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { toast } from 'sonner';

export const ConnectorCard = ({ connector, onConnect, onDisconnect }) => {
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const handleConnect = () => {
    setConnecting(true);
    setTimeout(() => {
      setConnecting(false);
      onConnect?.(connector.id);
      toast.success(`Connected to ${connector.name}`);
    }, 2000);
  };

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      toast.success(`Synced ${connector.name}`);
    }, 1500);
  };

  const handleDisconnect = () => {
    onDisconnect?.(connector.id);
    toast.info(`Disconnected from ${connector.name}`);
  };

  const isConnected = connector.status === 'connected';
  const isAvailable = connector.status === 'available';
  const isComingSoon = connector.status === 'coming_soon';

  return (
    <div 
      className={`bg-white rounded-lg border border-[var(--tt-border)] p-5 transition-all ${
        isComingSoon ? 'opacity-50' : 'hover:shadow-md'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-3xl">{connector.icon}</div>
          <div>
            <h3 className="font-semibold" style={{ color: 'var(--tt-text)' }}>
              {connector.name}
            </h3>
            <p className="text-xs" style={{ color: 'var(--tt-text-muted)' }}>
              {connector.category}
            </p>
          </div>
        </div>
        {isConnected && (
          <StatusBadge status="resolved">Connected</StatusBadge>
        )}
        {isComingSoon && (
          <span className="text-xs px-2 py-1 rounded bg-[var(--tt-bg-alt)]" style={{ color: 'var(--tt-text-muted)' }}>
            {connector.coming_soon_date}
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-sm mb-4" style={{ color: 'var(--tt-text-muted)' }}>
        {connector.description}
      </p>

      {/* Connected Info */}
      {isConnected && connector.account && (
        <div className="mb-4 p-3 bg-[var(--tt-bg-alt)] rounded-lg space-y-2 text-xs">
          <div className="flex justify-between">
            <span style={{ color: 'var(--tt-text-muted)' }}>Account:</span>
            <span className="font-medium" style={{ color: 'var(--tt-text-body)' }}>
              {connector.account}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--tt-text-muted)' }}>Last sync:</span>
            <span className="font-medium" style={{ color: 'var(--tt-text-body)' }}>
              {connector.last_sync}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--tt-text-muted)' }}>Items synced:</span>
            <span className="font-semibold" style={{ color: 'var(--tt-primary)' }}>
              {connector.items_synced?.toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="space-y-2">
        {isConnected && (
          <>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleSync}
                disabled={syncing}
                className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-[var(--tt-border)] hover:bg-[var(--tt-bg-alt)] transition-colors text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync'}
              </button>
              <button className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-[var(--tt-border)] hover:bg-[var(--tt-bg-alt)] transition-colors text-sm font-medium">
                <Settings className="w-4 h-4" />
                Settings
              </button>
            </div>
            <button
              onClick={handleDisconnect}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-[var(--tt-danger)] text-[var(--tt-danger)] hover:bg-[var(--tt-danger-bg)] transition-colors text-sm font-medium"
            >
              <X className="w-4 h-4" />
              Disconnect
            </button>
          </>
        )}

        {isAvailable && (
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[var(--tt-primary)] text-white hover:bg-[var(--tt-primary-dark)] transition-all font-medium disabled:opacity-50"
          >
            {connecting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                Connect
              </>
            )}
          </button>
        )}

        {isComingSoon && (
          <div className="text-center text-sm py-2" style={{ color: 'var(--tt-text-muted)' }}>
            Available {connector.coming_soon_date}
          </div>
        )}
      </div>
    </div>
  );
};
