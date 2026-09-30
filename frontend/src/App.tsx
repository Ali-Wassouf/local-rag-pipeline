import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

import { Shell } from './components/Shell'
import { ChatScreen } from './screens/ChatScreen'
import { ProjectDetailScreen } from './screens/ProjectDetailScreen'
import { ProjectsListScreen } from './screens/ProjectsListScreen'
import { ReviewScreen } from './screens/ReviewScreen'
import { UploadScreen } from './screens/UploadScreen'

const queryClient = new QueryClient()

type View =
  | { screen: 'projects' }
  | { screen: 'project-detail'; projectId: number }
  | { screen: 'chat'; projectId: number; returnTo: View }
  | { screen: 'upload'; projectId?: number; returnTo: View }
  | { screen: 'review'; documentId: number; returnTo: View }

function App() {
  const [view, setView] = useState<View>({ screen: 'projects' })

  let content: React.ReactNode

  if (view.screen === 'projects') {
    content = (
      <ProjectsListScreen
        onSelectProject={(projectId) => setView({ screen: 'project-detail', projectId })}
        onUploadStandalone={() => setView({ screen: 'upload', returnTo: view })}
      />
    )
  } else if (view.screen === 'project-detail') {
    const detailView = view
    content = (
      <ProjectDetailScreen
        projectId={detailView.projectId}
        onReviewDocument={(documentId) =>
          setView({ screen: 'review', documentId, returnTo: detailView })
        }
        onUploadHere={() =>
          setView({ screen: 'upload', projectId: detailView.projectId, returnTo: detailView })
        }
        onOpenChat={() =>
          setView({ screen: 'chat', projectId: detailView.projectId, returnTo: detailView })
        }
        onBack={() => setView({ screen: 'projects' })}
      />
    )
  } else if (view.screen === 'chat') {
    const chatView = view
    content = <ChatScreen projectId={chatView.projectId} onBack={() => setView(chatView.returnTo)} />
  } else if (view.screen === 'upload') {
    const uploadView = view
    content = (
      <UploadScreen
        projectId={uploadView.projectId}
        onReviewDocument={(documentId) =>
          setView({ screen: 'review', documentId, returnTo: uploadView.returnTo })
        }
        onBack={() => setView(uploadView.returnTo)}
      />
    )
  } else {
    const reviewView = view
    content = (
      <div>
        <div className="mx-auto max-w-4xl p-4">
          <button
            type="button"
            onClick={() => setView(reviewView.returnTo)}
            className="text-sm text-blue-600 hover:underline"
          >
            &larr; Back
          </button>
        </div>
        <ReviewScreen documentId={reviewView.documentId} />
      </div>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Shell>{content}</Shell>
    </QueryClientProvider>
  )
}

export default App
