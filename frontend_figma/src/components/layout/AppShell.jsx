import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppShell = ({ title, children }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-[var(--tt-bg)]">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
