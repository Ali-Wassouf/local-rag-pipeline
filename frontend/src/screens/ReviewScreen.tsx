import { useState } from 'react'

import { useSections, useUpdateSectionTitle } from '../api/hooks'
import type { SectionRead } from '../api/types'

interface ReviewScreenProps {
  documentId: number
  onBack: () => void
}

function EditableTitle({
  title,
  onSave,
}: {
  title: string
  onSave: (title: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(title)

  if (!editing) {
    return (
      <button
        type="button"
        className="cursor-pointer text-left font-serif text-sm text-ink hover:text-accent"
        onClick={() => {
          setDraft(title)
          setEditing(true)
        }}
      >
        {title}
      </button>
    )
  }

  function commit() {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed && trimmed !== title) {
      onSave(trimmed)
    }
  }

  return (
    <input
      autoFocus
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') commit()
        if (event.key === 'Escape') setEditing(false)
      }}
      className="border border-accent bg-paper px-1 font-serif text-sm text-ink focus:outline-none"
    />
  )
}

export function ReviewScreen({ documentId, onBack }: ReviewScreenProps) {
  const sectionsQuery = useSections(documentId)
  const updateTitle = useUpdateSectionTitle(documentId)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  function titleUpdateFailedFor(sectionId: number): boolean {
    return updateTitle.isError && updateTitle.variables?.sectionId === sectionId
  }

  const sections = sectionsQuery.data ?? []
  const selected = sections.find((s) => s.id === selectedId) ?? sections[0] ?? null

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <button
        type="button"
        onClick={onBack}
        className="cursor-pointer text-xs font-medium text-ink-secondary transition-colors hover:text-ink"
      >
        &larr; Back
      </button>

      <h1 className="mt-4 mb-6 font-serif text-3xl font-normal tracking-tight text-ink">
        Review structure
      </h1>

      <div className="flex gap-8">
        <div className="w-1/2">
          <h2 className="border-b border-rule pb-2 font-sans text-sm font-semibold text-ink">
            Structure
          </h2>
          {sectionsQuery.isLoading && <p className="pt-3 text-sm text-ink-muted">Loading…</p>}
          {sectionsQuery.isError && (
            <p className="pt-3 text-sm text-danger">{(sectionsQuery.error as Error).message}</p>
          )}
          <ul className="mt-2 space-y-0.5">
            {sections.map((section, index) => {
              const next: SectionRead | undefined = sections[index + 1]
              const hasGapAfter = next !== undefined && next.char_start > section.char_end
              const isSelected = selected?.id === section.id
              return (
                <li key={section.id}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedId(section.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') setSelectedId(section.id)
                    }}
                    style={{ paddingLeft: `${(section.depth - 1) * 16}px` }}
                    className={`flex cursor-pointer items-center justify-between rounded-md px-2 py-1.5 ${
                      isSelected ? 'bg-parchment' : 'hover:bg-parchment/60'
                    }`}
                  >
                    <EditableTitle
                      title={section.title}
                      onSave={(title) => updateTitle.mutate({ sectionId: section.id, title })}
                    />
                    <span className="flex items-center gap-2 font-mono text-xs tabular-nums text-ink-muted">
                      {section.source === 'manual' && (
                        <span className="rounded-sm bg-accent/10 px-1 text-accent">manual</span>
                      )}
                      {section.estimated_chunks} chunk{section.estimated_chunks === 1 ? '' : 's'}
                    </span>
                  </div>
                  {titleUpdateFailedFor(section.id) && (
                    <p
                      style={{ paddingLeft: `${section.depth * 16}px` }}
                      className="px-2 py-1 text-xs text-danger"
                    >
                      Couldn&rsquo;t save: {(updateTitle.error as Error).message}
                    </p>
                  )}
                  {hasGapAfter && (
                    <div
                      style={{ paddingLeft: `${section.depth * 16}px` }}
                      className="px-2 py-1 font-serif text-xs text-danger italic"
                    >
                      Untitled region
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </div>

        <div className="w-1/2 border-l border-rule pl-6">
          <h2 className="border-b border-rule pb-2 font-sans text-sm font-semibold text-ink">
            Preview
          </h2>
          {selected ? (
            <div className="mt-3">
              <p className="font-mono text-xs text-ink-muted">{selected.display_path}</p>
              <pre className="mt-2 font-serif text-sm whitespace-pre-wrap text-ink-secondary">
                {selected.preview}
              </pre>
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink-muted">Select a section to preview it.</p>
          )}
        </div>
      </div>
    </div>
  )
}
