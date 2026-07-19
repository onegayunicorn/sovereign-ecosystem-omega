/**
 * Aura Pulse — Sovereign UI Component
 * Galaxy A17 Interface Theme
 * 
 * Version: 3.0
 * Theme: Aura Pulse
 */

import React, { useEffect, useState } from 'react';

// Quantum Constants
const QUANTUM_COHERENCE = 0.947;
const QUANTUM_SIGNATURE = 'SOVEREIGN_Ω';

// Color Palette
const COLORS = {
  quantumBlue: '#00d4ff',
  auraPurple: '#9d50bb',
  deepObsidian: '#05060d',
  royalBlue: '#2563eb',
  emerald: '#10b981',
  amber: '#f59e0b',
  red: '#ef4444',
};

interface AuraPulseProps {
  children?: React.ReactNode;
  className?: string;
  pulseIntensity?: number;
  coherence?: number;
  status?: 'COHERENT' | 'DECOHERENT' | 'SCALING';
}

export const AuraPulse: React.FC<AuraPulseProps> = ({
  children,
  className = '',
  pulseIntensity = 1.0,
  coherence = QUANTUM_COHERENCE,
  status = 'COHERENT',
}) => {
  const [pulse, setPulse] = useState(0);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    const interval = setInterval(() => {
      setPulse(prev => (prev + 0.02) % (Math.PI * 2));
    }, 50);

    return () => {
      clearInterval(interval);
      setIsMounted(false);
    };
  }, []);

  const pulseValue = Math.sin(pulse) * 0.3 + 0.7;
  const coherenceOpacity = 0.6 + coherence * 0.4;
  const statusColor = status === 'COHERENT' ? COLORS.emerald : 
                      status === 'SCALING' ? COLORS.amber : COLORS.red;

  return (
    <div 
      className={`relative ${className}`}
      style={{
        background: `radial-gradient(ellipse at 50% 50%, rgba(0, 212, 255, 0.05), transparent 70%)`,
      }}
    >
      {/* Aura Glow */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 50% 50%, 
            rgba(157, 80, 187, ${0.05 * pulseValue * coherence}), 
            transparent 50%)`,
          transition: 'all 0.5s ease',
        }}
      />

      {/* Quantum Ring */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          border: `1px solid rgba(0, 212, 255, ${0.1 * pulseValue * coherence})`,
          borderRadius: '50%',
          transform: `scale(${0.8 + 0.2 * pulseValue})`,
          transition: 'all 0.5s ease',
        }}
      />

      {/* Status Indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <span 
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: statusColor }}
        />
        <span className="text-xs font-mono text-white/60">
          {status} · Φ {Math.round(coherence * 1000) / 1000}
        </span>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Signature */}
      <div className="absolute bottom-4 left-4 text-[10px] font-mono text-white/20">
        {QUANTUM_SIGNATURE} · v3.0
      </div>
    </div>
  );
};

// Sub-components
export const AuraPulseHeader: React.FC<{ title: string; subtitle?: string }> = ({ 
  title, 
  subtitle 
}) => (
  <div className="mb-6">
    <h1 className="text-2xl font-display font-bold text-white tracking-tight">
      {title}
    </h1>
    {subtitle && (
      <p className="text-sm text-white/50 font-mono">{subtitle}</p>
    )}
  </div>
);

export const AuraPulseCard: React.FC<{ 
  children: React.ReactNode; 
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-4 ${className}`}>
    {children}
  </div>
);

export const AuraPulseMetric: React.FC<{
  label: string;
  value: string | number;
  unit?: string;
  target?: string | number;
  status?: 'pass' | 'fail' | 'warning';
}> = ({ label, value, unit = '', target, status = 'pass' }) => {
  const statusColors = {
    pass: 'text-emerald-400',
    fail: 'text-red-400',
    warning: 'text-amber-400',
  };

  return (
    <div className="flex flex-col">
      <span className="text-xs font-mono text-white/40 uppercase tracking-wider">
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className={`text-xl font-bold font-mono ${statusColors[status]}`}>
          {value}
        </span>
        {unit && <span className="text-xs text-white/40 font-mono">{unit}</span>}
        {target && (
          <span className="text-[10px] text-white/30 font-mono">
            Target: {target}
          </span>
        )}
      </div>
    </div>
  );
};