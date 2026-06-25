/**
 * ResQNet AI - Sidebar Navigation
 * Premium dark sidebar with role-based navigation, active states, and micro-animations.
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, AlertTriangle, MapPin, Truck,
  Building2, Heart, Brain, BarChart3, FlaskConical,
  Settings, LogOut, Shield, ChevronLeft, ChevronRight,
  AlertOctagon,
} from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { ROLE_LABELS } from '../../lib/constants';
import type { UserRole } from '../../types';

interface NavItem {
  path: string;
  label: string;
  icon: typeof LayoutDashboard;
  minRole?: UserRole;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/report', label: 'Report Incident', icon: AlertOctagon },
  { path: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { path: '/map', label: 'Crisis Map', icon: MapPin },
  { path: '/resources', label: 'Resources', icon: Truck, minRole: 'field_officer' },
  { path: '/shelters', label: 'Shelters', icon: Building2, minRole: 'field_officer' },
  { path: '/hospitals', label: 'Hospitals', icon: Heart, minRole: 'field_officer' },
  { path: '/command-brief', label: 'Command Brief', icon: Brain, minRole: 'coordinator' },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, minRole: 'coordinator' },
  { path: '/simulation', label: 'Simulation', icon: FlaskConical, minRole: 'super_admin' },
  { path: '/settings', label: 'Settings', icon: Settings },
];

const ROLE_HIERARCHY: Record<string, number> = {
  citizen: 0, volunteer: 1, hospital: 2, shelter_manager: 2,
  field_officer: 3, coordinator: 4, gov_admin: 5, super_admin: 6,
};

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const userLevel = ROLE_HIERARCHY[user?.role || 'citizen'] || 0;

  const visibleItems = navItems.filter(item => {
    if (!item.minRole) return true;
    return userLevel >= (ROLE_HIERARCHY[item.minRole] || 0);
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <motion.aside
      animate={{ width: collapsed ? 70 : 260 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      style={{
        height: '100vh',
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-primary)',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 50,
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{
        padding: collapsed ? '16px 10px' : '16px 20px',
        borderBottom: '1px solid var(--border-primary)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        minHeight: '64px',
      }}>
        <div style={{
          width: '36px', height: '36px', minWidth: '36px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
          borderRadius: '10px',
          boxShadow: '0 0 15px rgba(59, 130, 246, 0.25)',
        }}>
          <Shield size={20} color="white" />
        </div>
        {!collapsed && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              ResQNet
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--color-primary-light)', fontWeight: 500, letterSpacing: '0.05em' }}>
              AI COMMAND CENTER
            </div>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {visibleItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: collapsed ? '10px' : '10px 14px',
              justifyContent: collapsed ? 'center' : 'flex-start',
              borderRadius: '8px',
              marginBottom: '2px',
              fontSize: '0.85rem',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
              background: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
              borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
              transition: 'all 0.15s',
              textDecoration: 'none',
            })}
          >
            <item.icon size={18} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User Section */}
      <div style={{
        padding: collapsed ? '12px 8px' : '12px 16px',
        borderTop: '1px solid var(--border-primary)',
      }}>
        {!collapsed && user && (
          <div style={{
            padding: '10px 12px',
            background: 'var(--bg-card)',
            borderRadius: '8px',
            marginBottom: '8px',
          }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user.full_name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-primary-light)', marginTop: '2px' }}>
              {ROLE_LABELS[user.role] || user.role}
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: '8px 12px',
            borderRadius: '8px',
            color: 'var(--text-muted)',
            background: 'transparent',
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; e.currentTarget.style.color = '#ef4444'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)'; }}
        >
          <LogOut size={18} />
          {!collapsed && <span style={{ fontSize: '0.85rem' }}>Sign Out</span>}
        </button>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        style={{
          position: 'absolute',
          top: '20px',
          right: '-12px',
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          zIndex: 51,
        }}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </motion.aside>
  );
}
