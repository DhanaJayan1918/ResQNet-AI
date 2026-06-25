/**
 * ResQNet AI - Main Layout
 * Wraps authenticated pages with sidebar + main content area.
 */

import { Outlet, Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import Sidebar from './Sidebar';
import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function MainLayout() {
  const { isAuthenticated, isLoading, loadUser } = useAuthStore();
  const [sidebarWidth, setSidebarWidth] = useState(260);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // Observe sidebar width changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const sidebar = document.querySelector('aside');
      if (sidebar) {
        setSidebarWidth(sidebar.getBoundingClientRect().width);
      }
    });

    const sidebar = document.querySelector('aside');
    if (sidebar) {
      observer.observe(sidebar, { attributes: true, attributeFilter: ['style'] });
      setSidebarWidth(sidebar.getBoundingClientRect().width);
    }

    return () => observer.disconnect();
  }, []);

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <Loader2
            size={40}
            color="var(--color-primary)"
            style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }}
          />
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading ResQNet AI...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        marginLeft: `${sidebarWidth}px`,
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        transition: 'margin-left 0.25s ease-in-out',
        overflowX: 'hidden',
      }}>
        <Outlet />
      </main>
    </div>
  );
}
