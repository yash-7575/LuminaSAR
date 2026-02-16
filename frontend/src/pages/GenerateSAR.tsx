import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { Zap, FileSearch, Loader2, CheckCircle, Brain, Database, Shield, Save, AlertCircle } from 'lucide-react'

const PIPELINE_STEPS = [
    { id: 1, name: 'Fetching Data', icon: Database, description: 'Loading customer KYC and transaction records from Supabase' },
    { id: 2, name: 'Analyzing Patterns', icon: FileSearch, description: 'Running ML algorithms: velocity, volume, structuring, network analysis' },
    { id: 3, name: 'Retrieving Templates', icon: Brain, description: 'RAG search in ChromaDB for relevant SAR templates' },
    { id: 4, name: 'Generating Narrative', icon: Zap, description: 'Ollama llama3.2 generating grounded SAR narrative' },
    { id: 5, name: 'Validating', icon: Shield, description: 'Cross-checking narrative against source data' },
    { id: 6, name: 'Saving Results', icon: Save, description: 'Persisting narrative and audit trail to database' },
]

export default function GenerateSAR() {
    const [searchParams] = useSearchParams()
    const [caseId, setCaseId] = useState(searchParams.get('case_id') || '')
    const [currentStep, setCurrentStep] = useState(0)
    const navigate = useNavigate()

    const generateMutation = useMutation({
        mutationFn: async (data: { case_id: string }) => {
            // Simulate step progression during generation
            const stepInterval = setInterval(() => {
                setCurrentStep(prev => Math.min(prev + 1, 6))
            }, 3000)

            setCurrentStep(1)
            try {
                const result = await api.generateSAR(data)
                clearInterval(stepInterval)
                setCurrentStep(6)
                return result
            } catch (err) {
                clearInterval(stepInterval)
                throw err
            }
        },
        onSuccess: (data) => {
            setTimeout(() => {
                navigate(`/editor/${data.narrative_id}`)
            }, 1500)
        },
    })

    const handleGenerate = () => {
        if (caseId.trim()) {
            generateMutation.mutate({ case_id: caseId.trim() })
        }
    }

    const isGenerating = generateMutation.isPending

    return (
        <div className="p-6 md:p-8 max-w-3xl mx-auto">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">
                    Generate <span className="gradient-text">SAR Report</span>
                </h1>
                <p className="text-slate-400">
                    Enter a Case ID to generate an AI-powered SAR narrative with full audit trail
                </p>
            </div>

            {/* Input Section */}
            {!isGenerating && !generateMutation.isSuccess && (
                <div className="glass-card p-8 animate-fade-in">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                        SAR Case ID
                    </label>
                    <input
                        type="text"
                        value={caseId}
                        onChange={(e) => setCaseId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                        placeholder="Paste your Case UUID here..."
                        className="w-full px-5 py-4 bg-slate-800/50 text-white rounded-xl
                       border border-slate-700/50 focus:border-cyan-500/50 
                       focus:ring-2 focus:ring-cyan-500/20 focus:outline-none
                       font-mono text-sm placeholder:text-slate-600
                       transition-all"
                    />

                    {generateMutation.isError && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-red-400 text-sm font-medium">Generation Failed</p>
                                <p className="text-red-400/70 text-xs mt-1">
                                    {(generateMutation.error as Error)?.message || 'An error occurred'}
                                </p>
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleGenerate}
                        disabled={!caseId.trim()}
                        className="w-full mt-6 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 
                       text-white font-semibold rounded-xl hover:scale-[1.02]
                       transition-all shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40
                       disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100
                       flex items-center justify-center gap-2 text-lg"
                    >
                        <Zap className="w-5 h-5" />
                        Generate SAR
                    </button>

                    <p className="text-center text-xs text-slate-600 mt-4">
                        ⚡ Powered by Ollama • llama3.2:latest • 100% Local • No data leaves your network
                    </p>
                </div>
            )}

            {/* Progress Section */}
            {(isGenerating || generateMutation.isSuccess) && (
                <div className="glass-card p-8 animate-fade-in">
                    {/* Overall Progress */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-3">
                            <span className="text-sm text-slate-400">Generation Progress</span>
                            <span className="text-sm font-mono text-cyan-400">
                                {Math.min(currentStep, 6)}/6 steps
                            </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full transition-all duration-1000"
                                style={{ width: `${(Math.min(currentStep, 6) / 6) * 100}%` }}
                            />
                        </div>
                    </div>

                    {/* Step Details */}
                    <div className="space-y-3">
                        {PIPELINE_STEPS.map((step) => {
                            const isComplete = currentStep > step.id
                            const isActive = currentStep === step.id
                            const isPending = currentStep < step.id

                            return (
                                <div
                                    key={step.id}
                                    className={`flex items-center gap-4 p-4 rounded-xl transition-all ${isActive ? 'bg-cyan-500/10 border border-cyan-500/20' :
                                            isComplete ? 'bg-green-500/5 border border-green-500/10' :
                                                'bg-slate-800/30 border border-transparent'
                                        }`}
                                >
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${isComplete ? 'bg-green-500/20' :
                                            isActive ? 'bg-cyan-500/20' :
                                                'bg-slate-700/50'
                                        }`}>
                                        {isComplete ? (
                                            <CheckCircle className="w-5 h-5 text-green-400" />
                                        ) : isActive ? (
                                            <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                                        ) : (
                                            <step.icon className="w-5 h-5 text-slate-500" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-medium ${isActive ? 'text-cyan-400' :
                                                isComplete ? 'text-green-400' :
                                                    'text-slate-500'
                                            }`}>
                                            {step.name}
                                        </p>
                                        <p className="text-xs text-slate-500 truncate">{step.description}</p>
                                    </div>
                                    <span className={`text-xs font-mono ${isComplete ? 'text-green-500' :
                                            isActive ? 'text-cyan-500' :
                                                'text-slate-600'
                                        }`}>
                                        {isComplete ? '✓' : isActive ? '...' : `${step.id}`}
                                    </span>
                                </div>
                            )
                        })}
                    </div>

                    {/* Success */}
                    {generateMutation.isSuccess && (
                        <div className="mt-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-center animate-fade-in">
                            <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
                            <p className="text-green-400 font-semibold">SAR Generated Successfully!</p>
                            <p className="text-green-400/60 text-sm mt-1">
                                Generated in {generateMutation.data?.generation_time_seconds}s with {generateMutation.data?.audit_steps} audit steps
                            </p>
                            <p className="text-slate-500 text-xs mt-2">Redirecting to editor...</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
