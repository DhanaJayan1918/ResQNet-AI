/**
 * ResQNet AI - Register Page
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import type { UserRole } from '../types';

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'citizen', label: 'Citizen' },
  { value: 'volunteer', label: 'Volunteer' },
  { value: 'field_officer', label: 'Field Officer' },
  { value: 'hospital', label: 'Hospital Staff' },
  { value: 'shelter_manager', label: 'Shelter Manager' },
];

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, isLoading, error, clearError } = useAuthStore();
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    organization: '',
    role: 'citizen' as UserRole,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleChange = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
    clearError();
    setValidationError('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      setValidationError('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      setValidationError('Password must be at least 8 characters');
      return;
    }
    try {
      await register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        phone: form.phone || undefined,
        organization: form.organization || undefined,
        role: form.role,
      });
      navigate('/dashboard');
    } catch {
      // handled by store
    }
  };

  const displayError = validationError || error;

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    background: 'var(--bg-input)',
    border: '1px solid var(--border-primary)',
    borderRadius: '8px',
    color: 'var(--text-primary)',
    fontSize: '0.875rem',
    transition: 'border-color 0.2s',
  };

  const labelStyle = {
    display: 'block' as const,
    fontSize: '0.8rem',
    fontWeight: 500,
    color: 'var(--text-secondary)',
    marginBottom: '6px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0a0e1a 0%, #111827 40%, #0f172a 100%)',
      position: 'relative',
      overflow: 'hidden',
      padding: '40px 0',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px)`,
        backgroundSize: '50px 50px',
      }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: '100%', maxWidth: '440px', padding: '0 20px', position: 'relative', zIndex: 1 }}
      >
        {/* Branding */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: '56px', height: '56px', background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            borderRadius: '14px', marginBottom: '12px', boxShadow: '0 0 30px rgba(59, 130, 246, 0.3)',
          }}>
            <Shield size={28} color="white" />
          </div>
          <h1 style={{
            fontSize: '1.5rem', fontWeight: 800,
            background: 'linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            Create Account
          </h1>
        </motion.div>

        {/* Form Card */}
        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }} className="glass" style={{ padding: '28px', borderRadius: '16px' }}>

          {displayError && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px',
              background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px', marginBottom: '16px', fontSize: '0.85rem', color: '#ef4444',
            }}>
              <AlertTriangle size={16} />
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '14px' }}>
              <label style={labelStyle}>Full Name</label>
              <input id="register-name" type="text" value={form.full_name}
                onChange={e => handleChange('full_name', e.target.value)}
                placeholder="Enter your full name" required style={inputStyle} />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={labelStyle}>Email</label>
              <input id="register-email" type="email" value={form.email}
                onChange={e => handleChange('email', e.target.value)}
                placeholder="you@example.com" required style={inputStyle} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
              <div>
                <label style={labelStyle}>Password</label>
                <div style={{ position: 'relative' }}>
                  <input id="register-password" type={showPassword ? 'text' : 'password'} value={form.password}
                    onChange={e => handleChange('password', e.target.value)}
                    placeholder="Min 8 chars" required style={{ ...inputStyle, paddingRight: '36px' }} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', color: 'var(--text-muted)', padding: '2px' }}>
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <div>
                <label style={labelStyle}>Confirm</label>
                <input id="register-confirm" type="password" value={form.confirmPassword}
                  onChange={e => handleChange('confirmPassword', e.target.value)}
                  placeholder="Re-enter password" required style={inputStyle} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
              <div>
                <label style={labelStyle}>Phone (Optional)</label>
                <input id="register-phone" type="tel" value={form.phone}
                  onChange={e => handleChange('phone', e.target.value)}
                  placeholder="+91-XXXXXXXXXX" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Organization</label>
                <input id="register-org" type="text" value={form.organization}
                  onChange={e => handleChange('organization', e.target.value)}
                  placeholder="Optional" style={inputStyle} />
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={labelStyle}>Role</label>
              <select id="register-role" value={form.role}
                onChange={e => handleChange('role', e.target.value)}
                style={{ ...inputStyle, cursor: 'pointer' }}>
                {ROLE_OPTIONS.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            <button id="register-submit" type="submit" disabled={isLoading} style={{
              width: '100%', padding: '12px',
              background: isLoading ? 'var(--border-secondary)' : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              color: 'white', borderRadius: '8px', fontWeight: 600, fontSize: '0.9rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              boxShadow: isLoading ? 'none' : '0 0 20px rgba(59, 130, 246, 0.3)',
            }}>
              {isLoading ? (
                <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Creating Account...</>
              ) : 'Create Account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--color-primary-light)', fontWeight: 500 }}>Sign In</Link>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
