import { AppShell } from '../components/layout/AppShell';
import { ConnectorGrid } from '../components/connectors/ConnectorGrid';
import { MOCK_CONNECTORS } from '../data/mockData';

export const ConnectorsPage = () => {
  return (
    <AppShell title="Connectors">
      <ConnectorGrid connectors={MOCK_CONNECTORS} />
    </AppShell>
  );
};
