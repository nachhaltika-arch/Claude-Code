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
    <div className="flex items-center gap-2">
      {phases.map((phase, index) => (
        <React.Fragment key={phase}>
          {index > 0 && (
            <div
              className={`flex-1 h-1 ${
                index <= currentIndex ? 'bg-kompagnon-600' : 'bg-gray-200'
              }`}
            />
          )}
          <div className="flex flex-col items-center gap-1">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                index < currentIndex
                  ? 'bg-success text-white'
                  : index === currentIndex
                  ? 'bg-kompagnon-600 text-white ring-2 ring-kompagnon-300'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {index < currentIndex ? (
                <CheckIcon className="w-6 h-6" />
              ) : (
                index + 1
              )}
            </div>
            <span className="text-xs font-medium text-center text-gray-600 whitespace-nowrap">
              {phaseLabels[phase]}
            </span>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}
