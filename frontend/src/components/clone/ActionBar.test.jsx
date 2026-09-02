import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ActionBar from './ActionBar';

vi.mock('../SearchableSelect', () => ({
  default: ({ value, onChange }) => (
    <select aria-label="Language" value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="Auto">Auto</option>
    </select>
  ),
}));

const labels = {
  'clone.quality': 'Quality',
  'clone.quality_fast': 'Fast',
  'clone.quality_balanced': 'Balanced',
  'clone.quality_studio': 'Studio',
  'clone.steps': 'Steps',
  'clone.synthesize': 'Synthesize Audio',
  'clone.download_audio': 'Download audio',
  'clone.speed': 'Speed',
};

function renderBar(overrides = {}) {
  const props = {
    simplified: true,
    t: (key) => labels[key] || key,
    language: 'Auto',
    setLanguage: vi.fn(),
    speed: 1,
    setSpeed: vi.fn(),
    steps: 16,
    setSteps: vi.fn(),
    showHearDemo: false,
    outputPlaying: false,
    isGenerating: false,
    handleGenerate: vi.fn(),
    handleDownload: vi.fn(),
    generationTime: 0,
    wasGeneratingRef: { current: false },
    ...overrides,
  };
  render(<ActionBar {...props} />);
  return props;
}

describe('Rich Future simplified action bar', () => {
  it('maps Fast, Balanced and Studio to 8, 16 and 32 inference steps', () => {
    const props = renderBar();

    fireEvent.click(screen.getByRole('button', { name: 'Fast' }));
    fireEvent.click(screen.getByRole('button', { name: 'Balanced' }));
    fireEvent.click(screen.getByRole('button', { name: 'Studio' }));

    expect(props.setSteps).toHaveBeenNthCalledWith(1, 8);
    expect(props.setSteps).toHaveBeenNthCalledWith(2, 16);
    expect(props.setSteps).toHaveBeenNthCalledWith(3, 32);
  });

  it('shows a direct download action after generation finishes', () => {
    const props = renderBar({ lastOutput: 'abc123.wav' });
    fireEvent.click(screen.getByRole('button', { name: 'Download audio WAV' }));
    fireEvent.click(screen.getByRole('button', { name: 'Download audio MP3' }));
    expect(props.handleDownload).toHaveBeenNthCalledWith(1, 'wav');
    expect(props.handleDownload).toHaveBeenNthCalledWith(2, 'mp3');
  });

  it('offers safe speaking-speed presets in simplified mode', () => {
    const props = renderBar();

    fireEvent.click(screen.getByRole('button', { name: '0.85×' }));
    fireEvent.click(screen.getByRole('button', { name: '1×' }));
    fireEvent.click(screen.getByRole('button', { name: '1.15×' }));

    expect(props.setSpeed).toHaveBeenNthCalledWith(1, 0.85);
    expect(props.setSpeed).toHaveBeenNthCalledWith(2, 1);
    expect(props.setSpeed).toHaveBeenNthCalledWith(3, 1.15);
  });
});
