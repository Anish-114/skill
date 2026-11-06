import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sparkles,
  Compass,
  Bookmark,
  User,
  Activity,
  CheckCircle2,
  AlertCircle,
  LogIn,
  LogOut,
  UserCheck,
  Users,
  Globe,
} from 'lucide-react';
import { cn } from '../utils/cn';

export type TabType = 'dashboard' | 'explore' | 'saved' | 'profile';

interface NavbarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  savedCount: number;
  serverHealthy: boolean | null;
  studentName?: string;
  isAuthenticated: boolean;
  onOpenAuthModal: () => void;
  onLogout: () => void;
  pendingTeamRequestsCount?: number;
  onOpenTeamRequests?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  savedCount,
  serverHealthy,
  studentName,
  isAuthenticated,
  onOpenAuthModal,
  onLogout,
  pendingTeamRequestsCount = 0,
  onOpenTeamRequests,
}) => {
  const { t, i18n } = useTranslation();

  const tabs = [
    { id: 'dashboard' as TabType, label: t('navbar.tab_dashboard'), icon: Sparkles },
    { id: 'explore' as TabType, label: t('navbar.tab_explore'), icon: Compass },
    { id: 'saved' as TabType, label: t('navbar.tab_saved'), icon: Bookmark, badge: savedCount > 0 ? savedCount : null },
    { id: 'profile' as TabType, label: t('navbar.tab_profile'), icon: User },
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

        {/* Right Status & Auth Actions */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Language Toggle */}
          <div className="flex items-center rounded-xl bg-slate-900 border border-slate-800 p-0.5 text-xs">
            <button
              onClick={() => i18n.changeLanguage('en')}
              className={cn(
                'px-2 py-1 rounded-lg font-bold transition-all text-[11px]',
                i18n.language === 'en'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              )}
              title="Switch to English"
            >
              EN
            </button>
            <button
              onClick={() => i18n.changeLanguage('hi-Latn')}
              className={cn(
                'px-2 py-1 rounded-lg font-bold transition-all text-[11px]',
                i18n.language === 'hi-Latn'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              )}
              title="Hinglish mein dekhein"
            >
              Hinglish
            </button>
          </div>

          {/* Team Requests Button */}
          {onOpenTeamRequests && (
            <button
              onClick={onOpenTeamRequests}
              className="relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
              title={t('navbar.team_requests')}
            >
              <Users className="w-3.5 h-3.5 text-brand-400" />
              <span className="hidden sm:inline">{t('navbar.team_requests')}</span>
              {pendingTeamRequestsCount > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-brand-500 text-white animate-pulse">
                  {pendingTeamRequestsCount}
                </span>
              )}
            </button>
          )}

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
              {serverHealthy
                ? t('navbar.server_online')
                : serverHealthy === false
                ? t('navbar.server_offline')
                : t('navbar.server_connecting')}
            </span>
          </div>

          {/* Student Profile & Switch User */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <button
              onClick={() => setActiveTab('profile')}
              className="flex items-center gap-2 text-left hover:opacity-85 transition-opacity"
              title="View & Edit Profile"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-700 to-indigo-600 border border-brand-500/30 flex items-center justify-center text-xs font-bold text-white shadow-sm">
                {studentName ? studentName.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden lg:flex flex-col">
                <span className="text-xs font-semibold text-slate-200 max-w-[110px] truncate">
                  {studentName || 'Student Profile'}
                </span>
                <span className="text-[10px] text-slate-400">
                  {isAuthenticated ? t('navbar.active_user') : t('navbar.demo_account')}
                </span>
              </div>
            </button>

            {/* Auth Action Button */}
            {isAuthenticated ? (
              <button
                onClick={onLogout}
                title="Log out and switch to demo"
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={onOpenAuthModal}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-600/90 hover:bg-brand-500 text-white shadow-sm transition-all"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('navbar.sign_in_register')}</span>
              </button>
            )}

            {isAuthenticated && (
              <button
                onClick={onOpenAuthModal}
                className="hidden sm:flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors border border-slate-800"
                title="Switch User Account"
              >
                <UserCheck className="w-3 h-3 text-brand-400" />
                <span>{t('navbar.switch_user')}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
