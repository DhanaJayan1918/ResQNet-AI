/**
 * ResQNet AI - Report Incident Page
 * Provides a citizen and field officer portal to report emergency incidents.
 * Includes interactive maps, guide instructions, and responsive dark aesthetics.
 */

import { motion } from 'framer-motion';
import { AlertOctagon, ShieldAlert, PhoneCall, HelpCircle } from 'lucide-react';
import ReportForm from '../components/incidents/ReportForm';

export default function ReportIncidentPage() {
  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{ marginBottom: '28px' }}
      >
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: 700,
          background: 'linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <ShieldAlert className="text-red-500" size={28} />
          Emergency Report Portal
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
          File a crisis incident report. The ResQNet AI agent will analyze your report and triage it in real-time.
        </p>
      </motion.div>

      {/* Main Grid: Form + Instructions */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: '24px',
      }} className="lg:grid-cols-3">
        {/* Left/Middle Column: The Form */}
        <div className="lg:col-span-2">
          <ReportForm />
        </div>

        {/* Right Column: Information & Guidelines */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
        >
          {/* Emergency Helplines */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <PhoneCall size={18} className="text-blue-400" />
              Emergency Hotlines
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>National Emergency Number</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: '#ef4444' }}>112</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Police Department</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-primary-light)' }}>100</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Ambulance Services</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: '#10b981' }}>108</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Disaster Management</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: '#f59e0b' }}>1078</span>
              </div>
            </div>
          </div>

          {/* Reporting Guidelines */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <HelpCircle size={18} className="text-yellow-400" />
              Reporting Guidelines
            </h3>
            <ul style={{
              fontSize: '0.82rem',
              color: 'var(--text-secondary)',
              paddingLeft: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              listStyleType: 'disc',
            }}>
              <li>
                <strong>Provide details:</strong> Describe exactly what you see (e.g., flooding level, number of people trapped, visible injuries).
              </li>
              <li>
                <strong>Pin accurately:</strong> Pan/zoom the map and tap on the exact spot where the incident is occurring to assist responders.
              </li>
              <li>
                <strong>Add landmarks:</strong> Landmarks (like buildings, shops, towers) help responders locate the scene faster if GPS accuracy is low.
              </li>
              <li>
                <strong>Attach photos:</strong> If safe, take and upload clear photos of the scene. AI processes these to verify severity.
              </li>
            </ul>
          </div>

          {/* AI Intake Info */}
          <div style={{
            padding: '16px',
            background: 'rgba(59, 130, 246, 0.05)',
            border: '1px solid rgba(59, 130, 246, 0.15)',
            borderRadius: '10px',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'start',
            gap: '10px'
          }}>
            <AlertOctagon size={16} className="text-blue-400" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div>
              <p style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                ResQNet AI Analysis
              </p>
              <p>
                Each report is automatically parsed by Gemini, categorized for crisis type, deduplicated against existing records, and assigned a dynamic priority score for immediate command center routing.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
