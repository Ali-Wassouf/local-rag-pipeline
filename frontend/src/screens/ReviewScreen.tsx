import { useState } from 'react'

import { useSections, useUpdateSectionTitle } from '../api/hooks'
import type { SectionRead } from '../api/types'

interface ReviewScreenProps {
  documentId: number
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
        className="text-left text-sm text-gray-900 hover:underline dark:text-gray-100"
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
      className="border border-blue-400 px-1 text-sm"
    />
  )
}

export function ReviewScreen({ documentId }: ReviewScreenProps) {
  const sectionsQuery = useSections(documentId)
  const updateTitle = useUpdateSectionTitle(documentId)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  function titleUpdateFailedFor(sectionId: number): boolean {
    return updateTitle.isError && updateTitle.variables?.sectionId === sectionId
  }

  const sections = sectionsQuery.data ?? []
  const selected = sections.find((s) => s.id === selectedId) ?? sections[0] ?? null

  return (
    <div className="mx-auto flex max-w-4xl gap-6 p-8">
      <div className="w-1/2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Structure</h2>
        {sectionsQuery.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
        {sectionsQuery.isError && (
          <p className="text-sm text-red-600">{(sectionsQuery.error as Error).message}</p>
        )}
        <ul className="mt-2 space-y-1">
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
                  className={`flex items-center justify-between rounded px-2 py-1 ${
                    isSelected ? 'bg-blue-50 dark:bg-blue-950' : ''
                  }`}
                >
                  <EditableTitle
                    title={section.title}
                    onSave={(title) => updateTitle.mutate({ sectionId: section.id, title })}
                  />
                  <span className="flex items-center gap-2 text-xs text-gray-400">
                    {section.source === 'manual' && (
                      <span className="rounded bg-amber-100 px-1 text-amber-700">manual</span>
                    )}
                    {section.estimated_chunks} chunk{section.estimated_chunks === 1 ? '' : 's'}
                  </span>
                </div>
                {titleUpdateFailedFor(section.id) && (
                  <p
                    style={{ paddingLeft: `${section.depth * 16}px` }}
                    className="px-2 py-1 text-xs text-red-600"
                  >
                    Couldn&rsquo;t save: {(updateTitle.error as Error).message}
                  </p>
                )}
                {hasGapAfter && (
                  <div
                    style={{ paddingLeft: `${section.depth * 16}px` }}
                    className="px-2 py-1 text-xs italic text-red-500"
                  >
                    Untitled region
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      </div>

      <div className="w-1/2 border-l border-gray-200 pl-6 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Preview</h2>
        {selected ? (
          <div className="mt-2">
            <p className="text-xs text-gray-500">{selected.display_path}</p>
            <pre className="mt-2 whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
              {selected.preview}
            </pre>
          </div>
        ) : (
          <p className="mt-2 text-sm text-gray-500">Select a section to preview it.</p>
        )}
      </div>
    </div>
  )
}
