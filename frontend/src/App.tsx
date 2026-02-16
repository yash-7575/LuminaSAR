import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import GenerateSAR from './pages/GenerateSAR'
import SAREditor from './pages/SAREditor'
import Navbar from './components/Navbar'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <div className="min-h-screen bg-slate-950 bg-mesh">
                    <Navbar />
                    <main className="pt-16">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/generate" element={<GenerateSAR />} />
                            <Route path="/editor/:narrativeId" element={<SAREditor />} />
                        </Routes>
                    </main>
                </div>
            </BrowserRouter>
        </QueryClientProvider>
    )
}

export default App
