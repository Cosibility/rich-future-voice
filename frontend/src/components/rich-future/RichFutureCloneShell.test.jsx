import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import RichFutureCloneShell from './RichFutureCloneShell';

describe('RichFutureCloneShell', () => {
  it('shows only the three-step cloning workflow and runtime status', () => {
    render(
      <RichFutureCloneShell
        modelStatus="ready"
        audioPlayer={<div>player</div>}
        toolkit={<div>recent takes and pronunciation</div>}
      >
        <div>clone form</div>
      </RichFutureCloneShell>,
    );

    expect(screen.getByText(/Rich Future/)).toBeInTheDocument();
    expect(screen.getAllByText('Voice').length).toBeGreaterThan(0);
    expect(screen.getByText('Script')).toBeInTheDocument();
    expect(screen.getByText('Synthesize Audio')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByText('clone form')).toBeInTheDocument();
    expect(screen.getByText('recent takes and pronunciation')).toBeInTheDocument();
    expect(screen.getByText('player')).toBeInTheDocument();
  });
});
