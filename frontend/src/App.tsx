import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

import { ReviewScreen } from './screens/ReviewScreen'
import { UploadScreen } from './screens/UploadScreen'

const queryClient = new QueryClient()

function App() {
  const [reviewDocumentId, setReviewDocumentId] = useState<number | null>(null)

  if (reviewDocumentId !== null) {
    return (
      <QueryClientProvider client={queryClient}>
        <div className="mx-auto max-w-4xl p-4">
          <button
            type="button"
            onClick={() => setReviewDocumentId(null)}
            className="text-sm text-blue-600 hover:underline"
          >
            &larr; Back to upload
          </button>
        </div>
        <ReviewScreen documentId={reviewDocumentId} />
      </QueryClientProvider>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <UploadScreen onReviewDocument={setReviewDocumentId} />
    </QueryClientProvider>
  )
}

export default App
