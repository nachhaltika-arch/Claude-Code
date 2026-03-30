import React from 'react';
import { CheckIcon } from '@heroicons/react/24/solid';

const phaseLabels = {
  phase_1: 'Akquisition',
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
                  background: isDone || isCurrent ? 'var(--kc-rot)' : 'var(--kc-rand)',
                  transition: 'background var(--kc-transition-base)',
                }}
              />
            )}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--kc-space-2)' }}>
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: 'var(--kc-radius-full)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--kc-font-display)',
                  fontWeight: 700,
                  fontSize: 'var(--kc-text-sm)',
                  transition: 'all var(--kc-transition-base)',
                  ...(isDone
                    ? {
                        background: 'var(--kc-success)',
                        color: 'var(--kc-weiss)',
                      }
                    : isCurrent
                    ? {
                        background: 'var(--kc-rot)',
                        color: 'var(--kc-weiss)',
                        boxShadow: '0 0 0 3px var(--kc-rot-subtle)',
                      }
                    : {
                        background: 'var(--kc-hell)',
                        color: 'var(--kc-mittel)',
                        border: '1.5px solid var(--kc-rand)',
                      }),
                }}
              >
                {isDone ? <CheckIcon style={{ width: '18px', height: '18px' }} /> : index + 1}
              </div>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: isCurrent ? 700 : 500,
                  color: isCurrent ? 'var(--kc-rot)' : 'var(--kc-text-subtil)',
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
