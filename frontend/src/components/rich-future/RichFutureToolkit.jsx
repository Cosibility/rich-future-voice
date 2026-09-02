import { useEffect, useMemo, useState } from 'react';
import { BookOpen, Download, History, Play, Plus, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import { apiFetch, apiJson } from '../../api/client';
import { audioUrl } from '../../api/generate';
import { encodeAudio } from '../../api/stories';
import { browserDownload, downloadBlob } from '../../utils/download';
import { Button } from '../../ui';

const matchingLanguage = (entry, language) => {
  const scope = String(entry.scope || entry.language || '*')
    .trim()
    .toLowerCase();
  if (scope === '*') return true;
  if (!language || language === 'Auto') return false;
  return scope.slice(0, 2) === String(language).trim().toLowerCase().slice(0, 2);
};

const outputBaseName = (audioPath) => {
  const filename = String(audioPath || 'voice.wav')
    .split('/')
    .pop();
  return filename.replace(/\.[^.]+$/, '') || 'voice';
};

export default function RichFutureToolkit({
  history = [],
  language = 'Auto',
  playTake,
  deleteTake,
}) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState([]);
  const [term, setTerm] = useState('');
  const [replacement, setReplacement] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [downloading, setDownloading] = useState('');

  useEffect(() => {
    let cancelled = false;
    apiJson('/pronunciation')
      .then((rows) => {
        if (!cancelled) setEntries(Array.isArray(rows) ? rows : []);
      })
      .catch(() => {
        if (!cancelled) setEntries([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const takes = useMemo(
    () => history.filter((item) => item.mode === 'clone' || item.mode === 'design').slice(0, 5),
    [history],
  );
  const visibleEntries = useMemo(
    () =>
      entries
        .filter((entry) => matchingLanguage(entry, language))
        .slice(-4)
        .reverse(),
    [entries, language],
  );

  const savePronunciation = async (event) => {
    event.preventDefault();
    const cleanTerm = term.trim();
    if (!cleanTerm || isSaving) return;
    setIsSaving(true);
    try {
      const response = await apiFetch('/pronunciation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          term: cleanTerm,
          replacement: replacement.trim(),
          type: 'respelling',
          language: language && language !== 'Auto' ? language : '*',
          enabled: true,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const created = await response.json();
      setEntries((current) => [...current, created]);
      setTerm('');
      setReplacement('');
    } catch (error) {
      toast.error(t('pronunciation.save_error', { message: error?.message || '' }));
    } finally {
      setIsSaving(false);
    }
  };

  const removePronunciation = async (entry) => {
    try {
      const response = await apiFetch(`/pronunciation/${encodeURIComponent(entry.id)}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setEntries((current) => current.filter((item) => item.id !== entry.id));
    } catch (error) {
      toast.error(t('pronunciation.save_error', { message: error?.message || '' }));
    }
  };

  const downloadTake = async (item, format) => {
    const key = `${item.id}:${format}`;
    if (!item.audio_path || downloading) return;
    setDownloading(key);
    try {
      const baseName = outputBaseName(item.audio_path);
      if (format === 'wav') {
        await browserDownload(audioUrl(item.audio_path), `rich-future-${baseName}.wav`);
      } else {
        const response = await apiFetch(audioUrl(item.audio_path));
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const encoded = await encodeAudio(await response.blob(), 'mp3', '192k');
        downloadBlob(encoded, `rich-future-${baseName}.mp3`);
      }
    } catch (error) {
      toast.error(t('clone.download_failed', { message: error?.message || '' }));
    } finally {
      setDownloading('');
    }
  };

  return (
    <aside className="flex min-h-0 flex-col gap-3 border-l border-[var(--chrome-border)] bg-[color-mix(in_srgb,var(--chrome-accent)_3%,var(--chrome-bg))] p-3 max-[860px]:border-l-0 max-[860px]:border-t">
      <section className="min-h-0 flex-1">
        <h2 className="mb-2 flex items-center gap-2 text-xs font-semibold text-[var(--chrome-fg)]">
          <History size={14} /> {t('history.title')}
        </h2>
        <div className="flex max-h-[330px] flex-col gap-2 overflow-y-auto pr-1">
          {takes.length === 0 ? (
            <p className="py-5 text-center text-xs text-[var(--chrome-fg-dim)]">
              {t('history.empty')}
            </p>
          ) : (
            takes.map((item) => (
              <article
                key={item.id}
                data-testid={`rf-take-${item.id}`}
                className="rounded-lg border border-[var(--chrome-border)] bg-[var(--chrome-bg)] p-2"
              >
                <p className="mb-2 line-clamp-2 text-xs leading-5 text-[var(--chrome-fg-muted)]">
                  {item.text || item.audio_path}
                </p>
                <div className="grid grid-cols-4 gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => playTake?.(item)}
                    aria-label={t('history.play_take')}
                  >
                    <Play size={12} />
                  </Button>
                  {['wav', 'mp3'].map((format) => (
                    <Button
                      key={format}
                      variant="ghost"
                      size="sm"
                      loading={downloading === `${item.id}:${format}`}
                      onClick={() => downloadTake(item, format)}
                      aria-label={`${t('clone.download_audio')} ${format.toUpperCase()}`}
                    >
                      {downloading !== `${item.id}:${format}` && (
                        <span className="inline-flex items-center gap-1 text-[10px]">
                          <Download size={11} /> {format.toUpperCase()}
                        </span>
                      )}
                    </Button>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteTake?.(item.id, 'synth')}
                    aria-label={t('common.delete')}
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="flex-none rounded-lg border border-[var(--chrome-border)] bg-[var(--chrome-bg)] p-2.5">
        <h2 className="mb-2 flex items-center gap-2 text-xs font-semibold text-[var(--chrome-fg)]">
          <BookOpen size={14} /> {t('pronunciation.title')}
        </h2>
        <form className="grid gap-1.5" onSubmit={savePronunciation}>
          <input
            className="input-base text-xs"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder={t('pronunciation.term_placeholder')}
            aria-label={t('pronunciation.term')}
          />
          <div className="flex gap-1.5">
            <input
              className="input-base min-w-0 flex-1 text-xs"
              value={replacement}
              onChange={(event) => setReplacement(event.target.value)}
              placeholder={t('pronunciation.replacement_placeholder')}
              aria-label={t('pronunciation.replacement')}
            />
            <Button
              type="submit"
              variant="subtle"
              size="sm"
              loading={isSaving}
              disabled={!term.trim()}
              aria-label={t('pronunciation.add')}
            >
              {!isSaving && <Plus size={13} />}
            </Button>
          </div>
        </form>
        {visibleEntries.length > 0 && (
          <div className="mt-2 flex flex-col gap-1">
            {visibleEntries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-center gap-2 rounded-md bg-[var(--chrome-hover-bg)] px-2 py-1 text-[11px]"
              >
                <span className="min-w-0 flex-1 truncate text-[var(--chrome-fg-muted)]">
                  <strong className="text-[var(--chrome-fg)]">{entry.term}</strong> →{' '}
                  {entry.replacement || '—'}
                </span>
                <button
                  type="button"
                  className="text-[var(--chrome-fg-dim)] hover:text-[var(--color-danger)]"
                  onClick={() => removePronunciation(entry)}
                  aria-label={t('pronunciation.remove', { term: entry.term })}
                >
                  <Trash2 size={11} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </aside>
  );
}
