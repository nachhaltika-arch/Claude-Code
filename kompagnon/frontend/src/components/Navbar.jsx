import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: scrolled ? 'rgba(30,30,30,0.97)' : 'var(--text-primary)',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        boxShadow: scrolled ? '0 2px 12px rgba(0,0,0,0.15)' : 'none',
        transition: 'box-shadow var(--kc-transition-base), background var(--kc-transition-base)',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--kc-container-xl)',
          margin: '0 auto',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            textDecoration: 'none',
            color: 'var(--text-inverse)',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              width: '8px',
              height: '24px',
              background: 'var(--brand-primary)',
              borderRadius: 'var(--kc-radius-sm)',
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '18px',
              fontWeight: 700,
              letterSpacing: 'var(--kc-tracking-wide)',
            }}
          >
            KOMPAGNON
          </span>
        </Link>
        <span
          style={{
            fontSize: '11px',
            color: 'var(--text-tertiary)',
            letterSpacing: 'var(--kc-tracking-wide)',
            textTransform: 'uppercase',
          }}
        >
          Automation System
        </span>
      </div>
    </nav>
  );
}
