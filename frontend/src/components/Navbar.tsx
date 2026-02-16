import { Link, useLocation } from 'react-router-dom'
import { Sparkles, LayoutDashboard, FileText } from 'lucide-react'

export default function Navbar() {
    const location = useLocation()

    const isActive = (path: string) => location.pathname === path

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-slate-800/50">
            <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-3 group">
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-shadow">
                        <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold gradient-text leading-tight">LuminaSAR</h1>
                        <p className="text-[10px] text-slate-500 leading-tight tracking-wider">THE GLASS BOX AI</p>
                    </div>
                </Link>

                {/* Navigation */}
                <div className="flex items-center gap-1">
                    <Link
                        to="/"
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${isActive('/')
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                            }`}
                    >
                        <LayoutDashboard className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <Link
                        to="/generate"
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${isActive('/generate')
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                            }`}
                    >
                        <FileText className="w-4 h-4" />
                        Generate SAR
                    </Link>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-xs text-slate-500">Ollama Connected</span>
                </div>
            </div>
        </nav>
    )
}
