import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { UploadScreen } from './screens/UploadScreen'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <UploadScreen />
    </QueryClientProvider>
  )
}

export default App
