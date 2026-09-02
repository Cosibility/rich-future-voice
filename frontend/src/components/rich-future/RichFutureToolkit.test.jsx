import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import RichFutureToolkit from './RichFutureToolkit';
import { apiFetch, apiJson } from '../../api/client';

vi.mock('../../api/client', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    apiJson: vi.fn(),
    apiFetch: vi.fn(),
  };
});

vi.mock('../../api/stories', () => ({
  encodeAudio: vi.fn().mockResolvedValue(new Blob(['mp3'], { type: 'audio/mpeg' })),
}));

vi.mock('../../utils/download', () => ({
  browserDownload: vi.fn().mockResolvedValue('voice.wav'),
  downloadBlob: vi.fn(),
}));

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}));

const history = Array.from({ length: 6 }, (_, index) => ({
  id: `take-${index}`,
  mode: 'clone',
  text: `Take ${index}`,
  audio_path: `take-${index}.wav`,
})).concat({ id: 'dub', mode: 'dub', text: 'Dub', audio_path: 'dub.wav' });

describe('RichFutureToolkit', () => {
  beforeEach(() => {
    vi.mocked(apiJson).mockResolvedValue([]);
    vi.mocked(apiFetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        id: 'pron-1',
        term: 'Rich Future',
        replacement: 'Rích Phiu-chờ',
        language: 'Vietnamese',
        enabled: true,
      }),
    });
  });

  it('keeps the five newest voice takes and excludes dubbing jobs', async () => {
    render(<RichFutureToolkit history={history} />);
    await waitFor(() => expect(apiJson).toHaveBeenCalledWith('/pronunciation'));
    expect(screen.getAllByTestId(/^rf-take-/)).toHaveLength(5);
    expect(screen.queryByText('Take 5')).not.toBeInTheDocument();
    expect(screen.queryByText('Dub')).not.toBeInTheDocument();
  });

  it('saves a pronunciation correction for the selected language', async () => {
    render(<RichFutureToolkit history={[]} language="Vietnamese" />);

    fireEvent.change(screen.getByRole('textbox', { name: 'Term' }), {
      target: { value: 'Rich Future' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Replacement' }), {
      target: { value: 'Rích Phiu-chờ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add entry' }));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        '/pronunciation',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"language":"Vietnamese"'),
        }),
      ),
    );
    expect(await screen.findByText(/Rích Phiu-chờ/)).toBeInTheDocument();
  });
});
