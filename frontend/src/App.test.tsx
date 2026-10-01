import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the projects list by default', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /Projects/ })).toBeInTheDocument()
  })
})
