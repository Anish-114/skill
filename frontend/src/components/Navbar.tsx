import React from 'react';
import { Sparkles, Compass, Bookmark, User, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '../utils/cn';

export type TabType = 'dashboard' | 'explore' | 'saved' | 'profile';

interface NavbarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  savedCount: number;
  serverHealthy: boolean | null;
  studentName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  savedCount,
  serverHealthy,
  studentName,
}) => {
  const tabs = [
    { id: 'dashboard' as TabType, label: 'AI Recommendations', icon: Sparkles },
    { id: 'explore' as TabType, label: 'Explore Events', icon: Compass },
    { id: 'saved' as TabType, label: 'Saved', icon: Bookmark, badge: savedCount > 0 ? savedCount : null },
    { id: 'profile' as TabType, label: 'My Profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 bg-slate-950/85">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-600 via-ai-primary to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                SkillBridge
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-md bg-brand-500/10 text-brand-400 border border-brand-500/20">
                AI v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 -mt-0.5 hidden sm:block">
              Intelligent Career & Hackathon Discovery
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'relative flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-slate-800/90 text-white shadow-sm border border-slate-700/80'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                )}
              >
                <Icon className={cn('w-4 h-4', isActive ? 'text-brand-400' : 'text-slate-400')} />
                <span className="hidden md:inline">{tab.label}</span>
                {tab.badge && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs font-semibold rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
                    {tab.badge}
                  </span>
                )}
                {isActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-gradient-to-r from-brand-500 to-ai-primary rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Status & Profile Pill */}
        <div className="flex items-center gap-3">
          {/* Server status pill */}
          <div
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
              serverHealthy === true
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : serverHealthy === false
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            )}
            title={serverHealthy ? 'FastAPI & AI Engines Online' : 'Connecting to Backend...'}
          >
            {serverHealthy ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            ) : serverHealthy === false ? (
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            ) : (
              <Activity className="w-3.5 h-3.5 animate-spin text-amber-400" />
            )}
            <span className="hidden sm:inline">
              {serverHealthy ? 'AI Online' : serverHealthy === false ? 'Offline' : 'Connecting'}
            </span>
          </div>

          {/* Student Avatar Tag */}
          <div
            onClick={() => setActiveTab('profile')}
            className="cursor-pointer flex items-center gap-2 pl-2 border-l border-slate-800 hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-brand-300">
              {studentName ? studentName.charAt(0) : 'A'}
            </div>
            <span className="text-xs font-medium text-slate-300 hidden lg:inline max-w-[120px] truncate">
              {studentName || 'Student'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
