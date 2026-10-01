import type { ReactNode } from 'react'

interface ShellProps {
  children: ReactNode
}

/**
 * Persistent running head, present on every screen — the volume title a
 * printed monograph repeats atop each page. Everything below sits on the
 * same warm paper ground.
 */
export function Shell({ children }: ShellProps) {
  return (
    <div className="flex h-screen flex-col bg-paper text-ink dark:bg-paper-dark dark:text-ink-dark">
      <header className="shrink-0 border-b border-rule dark:border-rule-dark">
        <div className="mx-auto flex max-w-5xl items-baseline gap-2 px-4 py-2.5 sm:px-8">
          <span className="font-mono text-[11px] font-medium tracking-[0.2em] text-ink-muted uppercase dark:text-ink-muted-dark">
            Marginalia
          </span>
          <span className="text-ink-muted dark:text-ink-muted-dark" aria-hidden="true">
            &middot;
          </span>
          <span className="font-mono text-[11px] tracking-[0.15em] text-ink-muted/70 uppercase dark:text-ink-muted-dark/70">
            a private reading
          </span>
        </div>
      </header>
      {/* Each screen fills exactly this remaining height; a screen with its
          own internal scroll regions (like Chat) never needs this to
          scroll — it's a safety net for screens that don't bound their own
          height, so the page itself is never what scrolls. */}
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </div>
  )
}
