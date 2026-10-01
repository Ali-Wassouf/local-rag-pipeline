import type { ReactNode } from 'react'

interface ShellNav {
  projectName: string
  documentCount: number
  activeTab: 'corpus' | 'chat'
  onNavigateCorpus: () => void
  onNavigateChat: () => void
}

interface ShellProps {
  children: ReactNode
  nav?: ShellNav
  onNavigateHome: () => void
}

function NavLink({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`cursor-pointer border-b-2 py-1 text-xs font-medium whitespace-nowrap transition-colors ${
        active
          ? 'border-accent font-semibold text-ink'
          : 'border-transparent text-ink-secondary hover:border-rule-strong hover:text-ink'
      }`}
    >
      {children}
    </button>
  )
}

/**
 * The running head: a 3-zone top bar (brand — project tabs — nothing else)
 * present on every screen, matching the Marginalia reference. The tabs
 * only appear once a project is open — the Projects list itself has no
 * "current project" to scope them to.
 */
export function Shell({ children, nav, onNavigateHome }: ShellProps) {
  return (
    <div className="flex h-screen flex-col bg-paper text-ink">
      <header className="z-30 flex h-[60px] shrink-0 items-center justify-between gap-6 border-b border-rule bg-paper px-6">
        <button
          type="button"
          onClick={onNavigateHome}
          className="shrink-0 cursor-pointer font-serif text-2xl font-medium tracking-tight text-ink transition-colors hover:text-accent"
        >
          Marginalia
        </button>

        {nav && (
          <nav className="hidden min-w-0 flex-1 items-center gap-7 overflow-hidden md:flex">
            <span className="truncate font-serif text-sm text-ink-secondary italic">
              {nav.projectName}
            </span>
            <NavLink active={nav.activeTab === 'corpus'} onClick={nav.onNavigateCorpus}>
              Project Corpus ({nav.documentCount})
            </NavLink>
            <NavLink active={nav.activeTab === 'chat'} onClick={nav.onNavigateChat}>
              Reading Room (Chat)
            </NavLink>
          </nav>
        )}
      </header>

      {nav && (
        <div className="flex items-center justify-around gap-1 border-b border-rule bg-parchment px-2 py-2 text-xs font-medium md:hidden">
          <span className="truncate px-2 font-serif text-ink-secondary italic">
            {nav.projectName}
          </span>
          <button
            type="button"
            onClick={nav.onNavigateCorpus}
            className={`cursor-pointer rounded-sm px-2.5 py-1 ${
              nav.activeTab === 'corpus' ? 'bg-accent text-paper' : 'text-ink-secondary'
            }`}
          >
            Corpus
          </button>
          <button
            type="button"
            onClick={nav.onNavigateChat}
            className={`cursor-pointer rounded-sm px-2.5 py-1 ${
              nav.activeTab === 'chat' ? 'bg-accent text-paper' : 'text-ink-secondary'
            }`}
          >
            Chat
          </button>
        </div>
      )}

      {/* Each screen fills exactly this remaining height; a screen with its
          own internal scroll regions (like Chat) never needs this to
          scroll — it's a safety net for screens that don't bound their own
          height, so the page itself is never what scrolls. */}
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </div>
  )
}
