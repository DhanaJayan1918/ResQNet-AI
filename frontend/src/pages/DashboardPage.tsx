/**
 * ResQNet AI - Dashboard Page (Placeholder)
 * Full implementation in Phase 7.
 */

import { motion } from 'framer-motion';
import {
  AlertTriangle, Activity, Users, Truck, Building2,
  Heart, Shield, TrendingUp,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { ROLE_LABELS } from '../lib/constants';

const mockStats = [
  { label: 'Active Incidents', value: '12', icon: AlertTriangle, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
  { label: 'Critical Alerts', value: '3', icon: Activity, color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)' },
  { label: 'People Affected', value: '52.8K', icon: Users, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
  { label: 'Resources Deployed', value: '14', icon: Truck, color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  { label: 'Shelters Active', value: '4', icon: Building2, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' },
  { label: 'Hospitals Online', value: '3', icon: Heart, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)' },
  { label: 'Priority Score Avg', value: '82.4', icon: TrendingUp, color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)' },
  { label: 'Response Rate', value: '94%', icon: Shield, color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.1)' },
];

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '28px' }}
      >
        <h1 style={{
          fontSize: '1.75rem', fontWeight: 700,
          background: 'linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          Command Dashboard
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          Welcome back, <span style={{ color: 'var(--text-secondary)' }}>{user?.full_name}</span>
          {' '}• <span style={{ color: 'var(--color-primary-light)' }}>{user?.role ? ROLE_LABELS[user.role] : ''}</span>
        </p>
      </motion.div>

      {/* Critical Alert Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="animate-pulse-glow"
        style={{
          padding: '14px 20px',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '24px',
        }}
      >
        <div style={{
          width: '10px', height: '10px', borderRadius: '50%',
          background: '#ef4444', boxShadow: '0 0 8px rgba(239, 68, 68, 0.6)',
        }} />
        <span style={{ fontSize: '0.875rem', color: '#fca5a5' }}>
          <strong style={{ color: '#ef4444' }}>CRITICAL:</strong> Severe flooding in Velachery — 800+ people affected.
          Building collapse in Tambaram — 20 trapped. Waterborne disease outbreak at Perambur camp.
        </span>
      </motion.div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '28px',
      }}>
        {mockStats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + index * 0.05 }}
            className="card"
            style={{
              padding: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <div style={{
              width: '48px', height: '48px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: stat.bg, borderRadius: '12px',
            }}>
              <stat.icon size={22} color={stat.color} />
            </div>
            <div>
              <div style={{
                fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)',
                lineHeight: 1.1,
              }}>
                {stat.value}
              </div>
              <div style={{
                fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px',
              }}>
                {stat.label}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Content Grid Placeholder */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '20px',
      }}>
        {/* Live Incident Feed */}
        <motion.div
          initial={{ opacity: 0, x: -15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
          style={{ padding: '20px' }}
        >
          <h3 style={{
            fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)',
            marginBottom: '16px',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <Activity size={18} color="var(--color-primary)" />
            Live Incident Feed
          </h3>
          {[
            { id: 'RESQ-20260625-0001', type: '🌊 Flood', severity: 'CRITICAL', score: 94.5, text: 'Severe flooding in Velachery area — 800 families trapped', time: '2h ago' },
            { id: 'RESQ-20260625-0002', type: '🏚️ Collapse', severity: 'CATASTROPHIC', score: 89.0, text: 'Building collapse at Tambaram — 20 workers trapped', time: '1h ago' },
            { id: 'RESQ-20260625-0003', type: '🏥 Medical', severity: 'CRITICAL', score: 86.0, text: 'Waterborne disease outbreak at Perambur relief camp', time: '3h ago' },
            { id: 'RESQ-20260625-0004', type: '🚨 Evacuation', severity: 'HIGH', score: 78.5, text: 'Adyar River bank evacuation — 500 families at risk', time: '5h ago' },
            { id: 'RESQ-20260625-0005', type: '⚡ Power', severity: 'HIGH', score: 72.0, text: 'Widespread power outage across Adyar — 50K affected', time: '30m ago' },
          ].map((inc, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '12px', borderRadius: '8px',
              background: i === 0 ? 'rgba(239, 68, 68, 0.06)' : 'transparent',
              borderBottom: '1px solid var(--border-primary)',
              transition: 'background 0.2s',
              cursor: 'pointer',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
            onMouseLeave={e => (e.currentTarget.style.background = i === 0 ? 'rgba(239, 68, 68, 0.06)' : 'transparent')}
            >
              <div style={{
                width: '36px', height: '36px', display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                background: inc.severity === 'CATASTROPHIC' ? 'rgba(220, 38, 38, 0.15)' :
                  inc.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(249, 115, 22, 0.12)',
                borderRadius: '8px', fontSize: '1.1rem',
              }}>
                {inc.type.split(' ')[0]}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {inc.text}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {inc.id} • {inc.time}
                </div>
              </div>
              <div style={{
                padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                background: inc.score >= 90 ? 'rgba(239, 68, 68, 0.15)' :
                  inc.score >= 80 ? 'rgba(249, 115, 22, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                color: inc.score >= 90 ? '#ef4444' :
                  inc.score >= 80 ? '#f97316' : '#eab308',
              }}>
                {inc.score}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Resource Status */}
        <motion.div
          initial={{ opacity: 0, x: 15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="card"
          style={{ padding: '20px' }}
        >
          <h3 style={{
            fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)',
            marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <Truck size={18} color="var(--color-accent)" />
            Resource Status
          </h3>
          {[
            { name: 'Ambulances', available: 3, total: 4, icon: '🚑' },
            { name: 'Rescue Boats', available: 1, total: 2, icon: '🚤' },
            { name: 'Medical Teams', available: 0, total: 2, icon: '👨‍⚕️' },
            { name: 'Fire Units', available: 1, total: 2, icon: '🚒' },
            { name: 'Helicopters', available: 1, total: 1, icon: '🚁' },
            { name: 'Generators', available: 0, total: 2, icon: '🔋' },
            { name: 'Volunteers', available: 1, total: 2, icon: '🤝' },
          ].map((res, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '8px 0', borderBottom: '1px solid var(--border-primary)',
            }}>
              <span style={{ fontSize: '1.1rem' }}>{res.icon}</span>
              <span style={{ flex: 1, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{res.name}</span>
              <span style={{
                fontSize: '0.78rem', fontWeight: 600, fontFamily: 'var(--font-mono)',
                color: res.available === 0 ? '#ef4444' : res.available <= 1 ? '#f97316' : '#22c55e',
              }}>
                {res.available}/{res.total}
              </span>
              <div style={{
                width: '50px', height: '4px', background: 'var(--border-primary)',
                borderRadius: '2px', overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${(res.available / res.total) * 100}%`,
                  background: res.available === 0 ? '#ef4444' : res.available <= 1 ? '#f97316' : '#22c55e',
                  borderRadius: '2px',
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
