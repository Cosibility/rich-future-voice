import { useTranslation } from 'react-i18next';
import { Fingerprint } from 'lucide-react';
import VoiceStudioMark from '../brand/VoiceStudioMark';

const STATUS_TONE = {
  ready: 'bg-[var(--color-success)]',
  loading: 'bg-[var(--color-warning,#fabd2f)]',
  idle: 'bg-[var(--chrome-fg-dim)]',
};

export default function RichFutureCloneShell({ modelStatus, children, audioPlayer, toolkit }) {
  const { t } = useTranslation();
  const status = modelStatus === 'ready' || modelStatus === 'loading' ? modelStatus : 'idle';

  return (
    <div className="rich-future-clone-app">
      <header className="flex min-h-[64px] items-center justify-between gap-4 border-b border-[var(--chrome-border)] bg-[var(--chrome-bg)] px-5 max-[520px]:px-3">
        <div className="flex min-w-0 items-center gap-3" translate="no">
          <VoiceStudioMark className="size-9 shrink-0 overflow-visible text-[var(--chrome-accent)]" />
          <div className="min-w-0">
            <div className="truncate text-base font-semibold tracking-[0.01em] text-[var(--chrome-fg)]">
              Rich Future <span className="text-[var(--chrome-accent)]">Voice</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-[var(--chrome-fg-muted)]">
              <Fingerprint size={11} /> {t('nav.voice')}
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 rounded-full border border-[var(--chrome-border)] px-3 py-1.5 text-[11px] text-[var(--chrome-fg-muted)]">
          <span className={`size-2 rounded-full ${STATUS_TONE[status]}`} aria-hidden="true" />
          {t(`header.status_${status}`)}
        </div>
      </header>

      <main className="min-h-0 overflow-y-auto bg-[var(--color-bg)] px-3 py-4 sm:px-5">
        <div
          className={`mx-auto flex min-h-full w-full flex-col overflow-hidden rounded-2xl border border-[var(--chrome-border)] bg-[var(--chrome-bg)] shadow-[0_18px_55px_rgba(0,0,0,0.22)] ${toolkit ? 'max-w-[1180px]' : 'max-w-[900px]'}`}
        >
          <div className="grid grid-cols-3 border-b border-[var(--chrome-border)] bg-[color-mix(in_srgb,var(--chrome-accent)_5%,var(--chrome-bg))] text-center text-[11px] font-medium text-[var(--chrome-fg-muted)]">
            {[t('clone.voice_kicker'), t('clone.script'), t('clone.synthesize')].map(
              (label, index) => (
                <div key={label} className="flex items-center justify-center gap-1.5 px-2 py-2.5">
                  <span className="inline-flex size-5 items-center justify-center rounded-full bg-[var(--chrome-accent-bg)] text-[10px] font-bold text-[var(--chrome-accent)]">
                    {index + 1}
                  </span>
                  <span className="truncate">{label}</span>
                </div>
              ),
            )}
          </div>
          <div
            className={`min-h-0 flex-1 ${toolkit ? 'grid grid-cols-[minmax(0,1fr)_300px] max-[860px]:grid-cols-1' : 'flex flex-col'}`}
          >
            <div className="flex min-h-0 flex-col p-2 sm:p-3">{children}</div>
            {toolkit}
          </div>
        </div>
      </main>

      {audioPlayer}
    </div>
  );
}
