import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, LogIn, UserPlus, Sparkles, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { login, register } from '../api/client';
import { StudentProfile, UserAccount, LoginPayload, RegisterPayload } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (profile: StudentProfile, user: UserAccount) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthSuccess }) => {
  const { t } = useTranslation();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form state
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regDegree, setRegDegree] = useState('B.Tech');
  const [regBranch, setRegBranch] = useState('Computer Science');
  const [regYear, setRegYear] = useState<number>(2);
  const [regCollege, setRegCollege] = useState('');

  if (!isOpen) return null;

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const payload: LoginPayload = {
        email: loginEmail.trim(),
        password: loginPassword,
      };
      const res = await login(payload);
      setSuccessMessage(`Welcome back, ${res.user.full_name}!`);
      setTimeout(() => {
        if (res.user.profile) {
          onAuthSuccess(res.user.profile, res.user);
        }
        onClose();
      }, 500);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setErrorMessage(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const payload: RegisterPayload = {
        full_name: regFullName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        degree: regDegree,
        branch: regBranch,
        year: Number(regYear),
        college_name: regCollege.trim() || undefined,
        experience_level: 'Beginner',
      };
      const res = await register(payload);
      setSuccessMessage(`Account created for ${res.user.full_name}!`);
      setTimeout(() => {
        if (res.user.profile) {
          onAuthSuccess(res.user.profile, res.user);
        }
        onClose();
      }, 500);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Registration failed. Please check your details.';
      setErrorMessage(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchToDemo = () => {
    setLoginEmail('student@skillbridge.ai');
    setLoginPassword('student123');
    setErrorMessage(null);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-md glass-panel bg-slate-950/95 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-6 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-100 text-base">
                {mode === 'login' ? t('auth.title_login') : t('auth.title_register')}
              </h3>
              <p className="text-xs text-slate-400">
                {mode === 'login' ? t('auth.subtitle_login') : t('auth.subtitle_register')}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="px-5 pt-4">
          <div className="grid grid-cols-2 p-1 bg-slate-900/90 rounded-xl border border-slate-800">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setErrorMessage(null);
              }}
              className={`flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'login'
                  ? 'bg-brand-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LogIn className="w-3.5 h-3.5" />
              {t('auth.tab_login')}
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setErrorMessage(null);
              }}
              className={`flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'register'
                  ? 'bg-brand-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              {t('auth.tab_register')}
            </button>
          </div>
        </div>

        {/* Alerts */}
        {errorMessage && (
          <div className="mx-5 mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="mx-5 mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Forms */}
        <div className="p-5">
          {mode === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">{t('auth.email')}</label>
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="student@university.edu"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">{t('auth.password')}</label>
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-2.5 px-4 rounded-xl font-semibold text-sm bg-gradient-to-r from-brand-600 via-indigo-600 to-indigo-500 text-white shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 hover:opacity-95 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? t('auth.signing_in') : t('auth.submit_login')}
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>

              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={handleSwitchToDemo}
                  className="text-xs text-brand-400 hover:text-brand-300 transition-colors underline underline-offset-2"
                >
                  {t('auth.switch_demo')}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.full_name')}</label>
                <input
                  type="text"
                  required
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  placeholder="e.g. Priya Patel"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.email')}</label>
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="priya@college.edu"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.password')}</label>
                  <input
                    type="password"
                    required
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    placeholder="Min 6 chars"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2.5">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.degree')}</label>
                  <select
                    value={regDegree}
                    onChange={(e) => setRegDegree(e.target.value)}
                    className="w-full px-2.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  >
                    <option value="B.Tech">B.Tech</option>
                    <option value="BCA">BCA</option>
                    <option value="B.E.">B.E.</option>
                    <option value="M.Tech">M.Tech</option>
                    <option value="MCA">MCA</option>
                    <option value="B.Sc">B.Sc</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.branch')}</label>
                  <input
                    type="text"
                    required
                    value={regBranch}
                    onChange={(e) => setRegBranch(e.target.value)}
                    placeholder="CS / IT / AI"
                    className="w-full px-2.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.academic_year')}</label>
                  <select
                    value={regYear}
                    onChange={(e) => setRegYear(Number(e.target.value))}
                    className="w-full px-2.5 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  >
                    <option value={1}>1st Year</option>
                    <option value={2}>2nd Year</option>
                    <option value={3}>3rd Year</option>
                    <option value={4}>4th Year</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">{t('auth.college_name')}</label>
                <input
                  type="text"
                  value={regCollege}
                  onChange={(e) => setRegCollege(e.target.value)}
                  placeholder="e.g. Delhi Technological University"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-2.5 px-4 rounded-xl font-semibold text-sm bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:opacity-95 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? t('auth.registering') : t('auth.submit_register')}
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
