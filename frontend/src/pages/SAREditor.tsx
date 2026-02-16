import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../services/api'
import {
    ShieldCheck, Clock, AlertTriangle, CheckCircle, Link2, Hash,
    ChevronDown, ChevronUp, ExternalLink, Eye, Fingerprint, Sparkles
} from 'lucide-react'

function RiskBadge({ score }: { score: number }) {
    const color = score >= 8 ? 'from-red-500 to-red-600' :
        score >= 5 ? 'from-orange-500 to-orange-600' :
            'from-green-500 to-green-600'
    return (
        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r ${color} shadow-lg`}>
            <AlertTriangle className="w-3.5 h-3.5 text-white" />
            <span className="text-sm font-bold text-white">{score}/10</span>
        </div>
    )
}

function AuditStepCard({ step, index, isExpanded, onToggle }: {
    step: any; index: number; isExpanded: boolean; onToggle: () => void
}) {
    const stepIcons: Record<string, any> = {
        fetch_data: '📥',
        analyze_patterns: '🔍',
        retrieve_templates: '📚',
        enrich_with_knowledge_graph: '🕸️',
        generate_narrative: '🤖',
        validate_narrative: '✅',
        save_results: '💾',
    }

    return (
        <div className="glass-card overflow-hidden glow-border">
            <button
                onClick={onToggle}
                className="w-full flex items-center gap-3 p-4 hover:bg-slate-800/30 transition-colors"
            >
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-lg flex-shrink-0">
                    {stepIcons[step.step_name] || '📋'}
                </div>
                <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-white capitalize">
                        {step.step_name.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-slate-500">
                        {step.logged_at ? new Date(step.logged_at).toLocaleString() : '—'}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-600">
                        #{index + 1}
                    </span>
                    {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-500" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                    )}
                </div>
            </button>

            {isExpanded && (
                <div className="px-4 pb-4 space-y-4 border-t border-slate-800/50 pt-4 animate-fade-in">
                    {/* Data Sources */}
                    <div>
                        <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <Link2 className="w-3 h-3" />
                            Data Sources
                        </h4>
                        <pre className="text-xs text-slate-300 bg-slate-900/50 rounded-lg p-3 overflow-x-auto font-mono">
                            {JSON.stringify(step.data_sources, null, 2)}
                        </pre>
                    </div>

                    {/* Reasoning */}
                    <div>
                        <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <Eye className="w-3 h-3" />
                            AI Reasoning
                        </h4>
                        <pre className="text-xs text-slate-300 bg-slate-900/50 rounded-lg p-3 overflow-x-auto font-mono">
                            {JSON.stringify(step.reasoning, null, 2)}
                        </pre>
                    </div>

                    {/* Hash Chain */}
                    <div className="flex items-center gap-2 pt-2 border-t border-slate-800/50">
                        <Fingerprint className="w-3.5 h-3.5 text-cyan-500" />
                        <span className="text-[10px] font-mono text-slate-600 truncate">
                            {step.current_hash?.substring(0, 24)}...
                        </span>
                    </div>
                </div>
            )}
        </div>
    )
}

export default function SAREditor() {
    const { narrativeId } = useParams<{ narrativeId: string }>()
    const [activeSentence, setActiveSentence] = useState<number | null>(null)
    const [expandedStep, setExpandedStep] = useState<number | null>(null)

    const { data: narrative, isLoading: narrativeLoading } = useQuery({
        queryKey: ['narrative', narrativeId],
        queryFn: () => api.getNarrative(narrativeId!),
        enabled: !!narrativeId,
    })

    const { data: audit, isLoading: auditLoading } = useQuery({
        queryKey: ['audit', narrativeId],
        queryFn: () => api.getAuditTrail(narrativeId!),
        enabled: !!narrativeId,
    })

    const approveMutation = useMutation({
        mutationFn: () => api.approveSAR(narrativeId!),
    })

    // Parse sentences from narrative
    const sentences = useMemo(() => {
        if (!narrative?.narrative_text) return []
        return narrative.narrative_text
            .split(/(?<=[.!?])\s+/)
            .filter((s: string) => s.trim().length > 0)
    }, [narrative?.narrative_text])

    // Get attribution for a sentence
    const getAttribution = (sentenceIndex: number) => {
        if (!audit?.sentence_attribution) return null
        const key = `sentence_${sentenceIndex}`
        return audit.sentence_attribution[key] || null
    }

    if (narrativeLoading || auditLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen">
                <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-slate-400">Loading SAR narrative...</p>
            </div>
        )
    }

    if (!narrative) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen">
                <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
                <p className="text-slate-400">Narrative not found</p>
            </div>
        )
    }

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Sparkles className="w-6 h-6 text-cyan-400" />
                        SAR Narrative Editor
                    </h1>
                    <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs text-slate-500 font-mono">
                            ID: {narrativeId?.substring(0, 8)}...
                        </span>
                        {narrative.risk_score != null && <RiskBadge score={narrative.risk_score} />}
                        <div className="flex gap-1">
                            {narrative.typologies?.map((t, i) => (
                                <span key={i} className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                    {t}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="flex gap-3">
                    {audit?.chain_valid !== undefined && (
                        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${audit.chain_valid
                            ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}>
                            {audit.chain_valid ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                            Hash chain {audit.chain_valid ? 'verified' : 'BROKEN'}
                        </div>
                    )}

                    <button
                        onClick={() => approveMutation.mutate()}
                        disabled={approveMutation.isPending || narrative.status === 'approved'}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600
                       text-white text-sm font-semibold rounded-lg hover:scale-105 transition-all
                       shadow-lg shadow-green-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        <CheckCircle className="w-4 h-4" />
                        {narrative.status === 'approved' ? 'Approved' :
                            approveMutation.isPending ? 'Approving...' : 'Approve SAR'}
                    </button>
                </div>
            </div>

            {/* Customer Info Banner */}
            {narrative.customer_name && (
                <div className="glass-card p-4 mb-6 flex flex-wrap items-center gap-6">
                    <div>
                        <span className="text-xs text-slate-500">Customer</span>
                        <p className="text-sm font-medium text-white">{narrative.customer_name}</p>
                    </div>
                    <div>
                        <span className="text-xs text-slate-500">Account</span>
                        <p className="text-sm font-mono text-slate-300">{narrative.customer_account}</p>
                    </div>
                    {narrative.generation_time_seconds != null && (
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-cyan-400" />
                            <span className="text-xs text-slate-400">Generated in {narrative.generation_time_seconds}s</span>
                        </div>
                    )}
                </div>
            )}

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left — Narrative with Sentence Attribution */}
                <div className="lg:col-span-2 glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-white">Generated Narrative</h2>
                        <span className="text-xs text-slate-500">
                            Click any sentence to see its data sources
                        </span>
                    </div>

                    <div className="prose prose-sm prose-invert max-w-none leading-relaxed text-slate-300">
                        {sentences.map((sentence: string, i: number) => {
                            const attr = getAttribution(i)
                            const hasRef = attr?.has_data_reference

                            return (
                                <span key={i}>
                                    <span
                                        className={`sentence-hover ${activeSentence === i ? 'active' : ''} ${hasRef ? 'border-l-cyan-500/40' : 'border-l-transparent'
                                            }`}
                                        onClick={() => setActiveSentence(activeSentence === i ? null : i)}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        {sentence.trim()}
                                        {hasRef && (
                                            <sup className="text-cyan-400 text-[10px] ml-0.5 font-mono">
                                                [{attr.transaction_ids?.length || attr.amounts?.length || 0}]
                                            </sup>
                                        )}
                                    </span>{'. '}
                                </span>
                            )
                        })}
                    </div>

                    {/* Active Sentence Attribution Detail */}
                    {activeSentence !== null && (
                        <div className="mt-6 p-4 bg-cyan-500/5 border border-cyan-500/20 rounded-xl animate-slide-in-up">
                            <div className="flex items-center gap-2 mb-3">
                                <Hash className="w-4 h-4 text-cyan-400" />
                                <span className="text-sm font-medium text-cyan-400">
                                    Sentence #{activeSentence + 1} Attribution
                                </span>
                            </div>

                            {(() => {
                                const attr = getAttribution(activeSentence)
                                if (!attr) {
                                    return <p className="text-xs text-slate-500">No attribution data available</p>
                                }

                                return (
                                    <div className="space-y-2">
                                        <p className="text-sm text-slate-300 bg-slate-900/50 p-2 rounded italic">
                                            "{attr.text}"
                                        </p>
                                        {attr.transaction_ids?.length > 0 && (
                                            <div className="flex flex-wrap gap-1">
                                                <span className="text-xs text-slate-500">Referenced TXNs:</span>
                                                {attr.transaction_ids.map((id: string, j: number) => (
                                                    <span key={j} className="text-xs font-mono bg-cyan-500/10 text-cyan-400 px-1.5 py-0.5 rounded">
                                                        {id.substring(0, 8)}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {attr.amounts?.length > 0 && (
                                            <p className="text-xs text-slate-400">
                                                <span className="text-slate-500">Amounts:</span>{' '}
                                                {attr.amounts.map((a: number) => `₹${a.toLocaleString()}`).join(', ')}
                                            </p>
                                        )}
                                        <p className="text-xs">
                                            <span className={`px-1.5 py-0.5 rounded ${attr.has_data_reference
                                                ? 'bg-green-500/10 text-green-400'
                                                : 'bg-yellow-500/10 text-yellow-400'
                                                }`}>
                                                {attr.has_data_reference ? '✓ Data-backed' : '⚠ No direct data reference'}
                                            </span>
                                        </p>
                                    </div>
                                )
                            })()}
                        </div>
                    )}
                </div>

                {/* Right — Audit Trail */}
                <div className="space-y-4">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-cyan-400" />
                        Audit Trail
                    </h2>

                    <div className="space-y-3">
                        {audit?.steps?.map((step, i) => (
                            <AuditStepCard
                                key={step.audit_id}
                                step={step}
                                index={i}
                                isExpanded={expandedStep === i}
                                onToggle={() => setExpandedStep(expandedStep === i ? null : i)}
                            />
                        ))}
                    </div>

                    {!audit?.steps?.length && (
                        <div className="glass-card p-6 text-center">
                            <p className="text-slate-500 text-sm">No audit trail found</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
