import React from 'react';

/**
 * Rich Future Voice's compact mark: a rising signal inside a soft frame.
 * Keep the legacy component name so engine-facing imports and persisted app
 * state remain compatible with the upstream VoiceStudio project.
 */
export default function VoiceStudioMark({ className = '', title, ...props }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <rect x="7" y="7" width="50" height="50" rx="16" stroke="currentColor" opacity="0.24" />
      <path d="M17 38V30M25 42V22M33 38V27" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
      <path
        d="M38 33 50 21m-9 0h9v9"
        stroke="currentColor"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
