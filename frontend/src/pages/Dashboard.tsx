import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Plus, TrendingUp, Clock, DollarSign, ShieldCheck, AlertTriangle, FileText, ChevronRight } from 'lucide-react'

function StatsWidget({ title, value, subtitle, icon: Icon, color }: {
    title: string
    value: string | number
    subtitle: string
    icon: any
    color: string
}) {
    return (
        <div className="glass-card p-5 glow-border animate-slide-in-up group hover:scale-[1.02] transition-transform">
            <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                    <Icon className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">{title}</span>
            </div>
            <p className="text-3xl font-bold text-white mb-1">{value}</p>
            <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
    )
}

function CaseRow({ caseData, onClick }: { caseData: any; onClick: () => void }) {
    const riskColor = (score: number) => {
        if (score >= 8) return 'text-red-400 bg-red-500/10'
        if (score >= 5) return 'text-orange-400 bg-orange-500/10'
        return 'text-green-400 bg-green-500/10'
    }

    const statusColor = (status: string) => {
        switch (status) {
            case 'approved': return 'text-green-400 bg-green-500/10 border-green-500/20'
            case 'generated': return 'text-blue-400 bg-blue-500/10 border-blue-500/20'
            default: return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
        }
    }

    return (
        <tr
            className="border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors group"
            onClick={onClick}
        >
            <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-medium text-cyan-400">
                        {caseData.customer_name?.[0] || '?'}
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">{caseData.customer_name}</p>
                        <p className="text-xs text-slate-500 font-mono">{caseData.customer_account}</p>
                    </div>
                </div>
            </td>
            <td className="py-4 px-4">
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${statusColor(caseData.status)}`}>
                    {caseData.status?.toUpperCase()}
                </span>
            </td>
            <td className="py-4 px-4">
                {caseData.risk_score != null ? (
                    <span className={`text-sm font-semibold px-2 py-0.5 rounded ${riskColor(caseData.risk_score)}`}>
                        {caseData.risk_score}/10
                    </span>
                ) : (
                    <span className="text-slate-600 text-sm">—</span>
                )}
            </td>
            <td className="py-4 px-4">
                <div className="flex flex-wrap gap-1">
                    {caseData.typologies?.slice(0, 2).map((t: string, i: number) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-300">
                            {t}
                        </span>
                    ))}
                </div>
            </td>
            <td className="py-4 px-4 text-sm text-slate-400">
                {caseData.created_at ? new Date(caseData.created_at).toLocaleDateString() : '—'}
            </td>
            <td className="py-4 px-4">
                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
            </td>
        </tr>
    )
}

export default function Dashboard() {
    const navigate = useNavigate()

    const { data: stats } = useQuery({
        queryKey: ['stats'],
        queryFn: api.getStats,
    })

    const { data: cases, isLoading: casesLoading } = useQuery({
        queryKey: ['recent-cases'],
        queryFn: api.getRecentCases,
    })

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                        Welcome to <span className="gradient-text">LuminaSAR</span>
                    </h1>
                    <p className="text-slate-400 text-sm md:text-base">
                        The Glass Box AI — Where Every Decision is Transparent
                    </p>
                </div>
                <button
                    onClick={() => navigate('/generate')}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 
                     text-white font-semibold rounded-xl hover:scale-105 
                     transition-all shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40"
                >
                    <Plus className="w-5 h-5" />
                    New SAR
                </button>
            </div>

            {/* Stats Widgets */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
                <StatsWidget
                    title="Total SARs"
                    value={stats?.total_sars || 0}
                    subtitle={`${stats?.pending_cases || 0} pending review`}
                    icon={FileText}
                    color="bg-gradient-to-br from-cyan-500 to-cyan-600"
                />
                <StatsWidget
                    title="Avg Time"
                    value={`${stats?.avg_generation_time || 0}s`}
                    subtitle="↓ 94% vs manual (5hrs)"
                    icon={Clock}
                    color="bg-gradient-to-br from-blue-500 to-blue-600"
                />
                <StatsWidget
                    title="Cost Savings"
                    value={`₹${stats?.cost_savings_lakhs || 0}L`}
                    subtitle="This year"
                    icon={DollarSign}
                    color="bg-gradient-to-br from-green-500 to-green-600"
                />
                <StatsWidget
                    title="High Risk"
                    value={stats?.high_risk_cases || 0}
                    subtitle="Cases scoring > 7/10"
                    icon={AlertTriangle}
                    color="bg-gradient-to-br from-orange-500 to-red-500"
                />
            </div>

            {/* Recent Cases */}
            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-slate-800/50 flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-cyan-400" />
                        Recent SAR Cases
                    </h2>
                    <span className="text-sm text-slate-500">{cases?.length || 0} cases</span>
                </div>

                {casesLoading ? (
                    <div className="p-12 text-center">
                        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                        <p className="text-slate-400 text-sm">Loading cases...</p>
                    </div>
                ) : cases && cases.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-800/50">
                                    <th className="py-3 px-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Customer</th>
                                    <th className="py-3 px-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="py-3 px-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Risk</th>
                                    <th className="py-3 px-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Typologies</th>
                                    <th className="py-3 px-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Created</th>
                                    <th className="py-3 px-4"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {cases.map((c) => (
                                    <CaseRow
                                        key={c.case_id}
                                        caseData={c}
                                        onClick={() => {
                                            if (c.has_narrative) {
                                                navigate(`/generate?case_id=${c.case_id}`)
                                            } else {
                                                navigate(`/generate?case_id=${c.case_id}`)
                                            }
                                        }}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center">
                        <FileText className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                        <p className="text-slate-400 mb-2">No SAR cases yet</p>
                        <p className="text-slate-500 text-sm mb-4">Generate synthetic data to get started</p>
                        <button
                            onClick={() => navigate('/generate')}
                            className="px-4 py-2 bg-cyan-500/10 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/20 transition-colors"
                        >
                            Generate Your First SAR →
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
