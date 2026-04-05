import React from 'react';
import { CheckIcon } from '@heroicons/react/24/solid';

const phaseLabels = {
  phase_1: 'Onboarding',
  phase_2: 'Briefing',
  phase_3: 'Content',
  phase_4: 'Technik',
  phase_5: 'QA',
  phase_6: 'Go-Live',
  phase_7: 'Post-Launch',
  completed: 'Fertig',
};

export default function PhaseTracker({ currentPhase = 'phase_1' }) {
  const phases = ['phase_1', 'phase_2', 'phase_3', 'phase_4', 'phase_5', 'phase_6', 'phase_7', 'completed'];
  const currentIndex = phases.indexOf(currentPhase);

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0 }}>
      {phases.map((phase, index) => {
        const isDone = index < currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <React.Fragment key={phase}>
            {index > 0 && (
              <div
                style={{
                  flex: 1,
                  height: '2px',
                  marginTop: '16px',
                  background: isDone || isCurrent ? 'var(--brand-primary)' : 'var(--border-light)',
                  transition: 'background var(--kc-transition-base)',
                }}
              />
            )}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: 'var(--radius-full)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-sans)',
                  fontWeight: 700,
                  fontSize: '13px',
                  transition: 'all var(--kc-transition-base)',
                  ...(isDone
                    ? {
                        background: 'var(--status-success-text)',
                        color: 'var(--bg-surface)',
                      }
                    : isCurrent
                    ? {
                        background: 'var(--brand-primary)',
                        color: 'var(--bg-surface)',
                        boxShadow: '0 0 0 3px var(--kc-rot-subtle)',
                      }
                    : {
                        background: 'var(--bg-app)',
                        color: 'var(--text-tertiary)',
                        border: '1.5px solid var(--border-light)',
                      }),
                }}
              >
                {isDone ? <CheckIcon style={{ width: '18px', height: '18px' }} /> : index + 1}
              </div>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: isCurrent ? 700 : 500,
                  color: isCurrent ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                  letterSpacing: 'var(--kc-tracking-wide)',
                  textTransform: 'uppercase',
                }}
              >
                {phaseLabels[phase]}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}
