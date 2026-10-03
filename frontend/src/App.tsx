import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

import { useProject, useProjectDocuments } from './api/hooks'
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

function projectIdForNav(view: View): number | null {
  if (view.screen === 'project-detail' || view.screen === 'chat') return view.projectId
  return null
}

function AppContent() {
  const [view, setView] = useState<View>({ screen: 'projects' })

  const navProjectId = projectIdForNav(view)
  const navProject = useProject(navProjectId)
  const navDocuments = useProjectDocuments(navProjectId)

  let content: React.ReactNode

  if (view.screen === 'projects') {
    content = (
      <ProjectsListScreen
        onSelectProject={(projectId) => setView({ screen: 'project-detail', projectId })}
        onOpenChat={(projectId) =>
          setView({ screen: 'chat', projectId, returnTo: { screen: 'project-detail', projectId } })
        }
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
      <ReviewScreen documentId={reviewView.documentId} onBack={() => setView(reviewView.returnTo)} />
    )
  }

  const nav =
    navProjectId !== null && (view.screen === 'project-detail' || view.screen === 'chat')
      ? {
          projectName: navProject.data?.name ?? '…',
          documentCount: navDocuments.data?.length ?? 0,
          activeTab: (view.screen === 'chat' ? 'chat' : 'corpus') as 'corpus' | 'chat',
          onNavigateCorpus: () => setView({ screen: 'project-detail', projectId: navProjectId }),
          onNavigateChat: () =>
            setView({
              screen: 'chat',
              projectId: navProjectId,
              returnTo: { screen: 'project-detail', projectId: navProjectId },
            }),
        }
      : undefined

  return (
    <Shell nav={nav} onNavigateHome={() => setView({ screen: 'projects' })}>
      {content}
    </Shell>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App
