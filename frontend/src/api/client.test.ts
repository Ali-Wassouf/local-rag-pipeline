import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getProject } from './client'

describe('API error messages', () => {
  const originalFetch = globalThis.fetch

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('surfaces a plain-string detail instead of the raw response body', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Project not found' }), {
        status: 404,
        statusText: 'Not Found',
      }),
    )

    await expect(getProject(1)).rejects.toThrow('Project not found')
  })

  it('joins a FastAPI validation error’s detail list into one message', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [
            { loc: ['body', 'name'], msg: 'field required', type: 'missing' },
            { loc: ['body', 'age'], msg: 'must be positive', type: 'value_error' },
          ],
        }),
        { status: 422, statusText: 'Unprocessable Entity' },
      ),
    )

    await expect(getProject(1)).rejects.toThrow('field required; must be positive')
  })

  it('falls back to the raw body when it is not JSON', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response('upstream gateway timeout', { status: 504, statusText: 'Gateway Timeout' }),
    )

    await expect(getProject(1)).rejects.toThrow('upstream gateway timeout')
  })

  it('falls back to the status line when the body is empty', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(new Response('', { status: 500, statusText: 'Internal Server Error' }))

    await expect(getProject(1)).rejects.toThrow('500 Internal Server Error')
  })
})
