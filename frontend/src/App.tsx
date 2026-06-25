/**
 * ResQNet AI - Root Application
 * React Router setup with auth guard and route definitions.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MainLayout from './components/layout/MainLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ReportIncidentPage from './pages/ReportIncidentPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/report" element={<ReportIncidentPage />} />
            {/* Phase 7 routes — placeholders */}
            <Route path="/incidents" element={<PlaceholderPage title="Incidents" icon="🚨" />} />
            <Route path="/map" element={<PlaceholderPage title="Crisis Map" icon="🗺️" />} />
            <Route path="/resources" element={<PlaceholderPage title="Resources" icon="🚑" />} />
            <Route path="/shelters" element={<PlaceholderPage title="Shelters" icon="🏠" />} />
            <Route path="/hospitals" element={<PlaceholderPage title="Hospitals" icon="🏥" />} />
            <Route path="/command-brief" element={<PlaceholderPage title="Command Brief" icon="🧠" />} />
            <Route path="/analytics" element={<PlaceholderPage title="Analytics" icon="📊" />} />
            <Route path="/simulation" element={<PlaceholderPage title="Crisis Simulation" icon="🧪" />} />
            <Route path="/settings" element={<PlaceholderPage title="Settings" icon="⚙️" />} />
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

/** Temporary placeholder for pages built in later phases */
function PlaceholderPage({ title, icon }: { title: string; icon: string }) {
  return (
    <div style={{
      padding: '40px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '4rem', marginBottom: '16px' }}>{icon}</div>
      <h1 style={{
        fontSize: '1.5rem',
        fontWeight: 700,
        color: 'var(--text-primary)',
        marginBottom: '8px',
      }}>
        {title}
      </h1>
      <p style={{
        color: 'var(--text-muted)',
        fontSize: '0.9rem',
        maxWidth: '400px',
      }}>
        This module is under active development and will be available in the next phase.
      </p>
    </div>
  );
}

export default App;
