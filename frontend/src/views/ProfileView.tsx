import React, { useState } from 'react';
import {
  User,
  GraduationCap,
  Sparkles,
  Plus,
  Trash2,
  Check,
  Save,
  BookOpen,
  Award,
  Link,
  Github,
  Linkedin,
} from 'lucide-react';
import { StudentProfile, StudentSkillItem } from '../types';
import {
  updateProfile,
  addOrUpdateSkill,
  deleteSkill,
  parseBio,
} from '../api/client';
import { cn } from '../utils/cn';

interface ProfileViewProps {
  profile: StudentProfile | null;
  onProfileUpdated: (updated: StudentProfile) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  profile,
  onProfileUpdated,
}) => {
  if (!profile) return null;

  // Form state
  const [formData, setFormData] = useState({
    degree: profile.degree || 'B.Tech',
    branch: profile.branch || 'Computer Science & Engineering',
    year: profile.year || 3,
    cgpa: profile.cgpa ?? 8.5,
    experience_level: profile.experience_level || 'Intermediate',
    college_name: profile.college_name || '',
    raw_bio: profile.raw_bio || '',
    github_url: profile.github_url || '',
    linkedin_url: profile.linkedin_url || '',
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Skill Add Form State
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillLevel, setNewSkillLevel] = useState('Intermediate');
  const [newSkillExp, setNewSkillExp] = useState(1.0);
  const [addingSkill, setAddingSkill] = useState(false);

  // NLP Extracted Skills State
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [parsingBio, setParsingBio] = useState(false);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await updateProfile(formData);
      onProfileUpdated(res);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update profile:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddSkill = async (nameToAdd?: string) => {
    const targetName = nameToAdd || newSkillName;
    if (!targetName.trim()) return;

    setAddingSkill(true);
    try {
      const added = await addOrUpdateSkill({
        name: targetName.trim(),
        proficiency_level: newSkillLevel,
        years_of_experience: Number(newSkillExp),
        verified: true,
      });

      // Update local profile state
      const existingIdx = profile.skills.findIndex(
        (s) => s.name.toLowerCase() === added.name.toLowerCase()
      );
      let updatedSkills: StudentSkillItem[];
      if (existingIdx >= 0) {
        updatedSkills = [...profile.skills];
        updatedSkills[existingIdx] = added;
      } else {
        updatedSkills = [...profile.skills, added];
      }

      onProfileUpdated({ ...profile, skills: updatedSkills });
      setNewSkillName('');
      // Remove from extracted if present
      setExtractedSkills((prev) => prev.filter((s) => s !== targetName));
    } catch (err) {
      console.error('Failed to add skill:', err);
    } finally {
      setAddingSkill(false);
    }
  };

  const handleDeleteSkill = async (skillId?: number) => {
    if (!skillId) return;
    try {
      await deleteSkill(skillId);
      const updatedSkills = profile.skills.filter((s) => s.skill_id !== skillId);
      onProfileUpdated({ ...profile, skills: updatedSkills });
    } catch (err) {
      console.error('Failed to delete skill:', err);
    }
  };

  const handleExtractBioSkills = async () => {
    if (!formData.raw_bio.trim()) return;
    setParsingBio(true);
    try {
      const result = await parseBio(formData.raw_bio);
      // Filter out skills the student already has
      const currentNames = new Set(profile.skills.map((s) => s.name.toLowerCase()));
      const unadded = result.extracted_skills.filter(
        (s) => !currentNames.has(s.toLowerCase())
      );
      setExtractedSkills(unadded);
    } catch (err) {
      console.error('Failed to extract skills from bio:', err);
    } finally {
      setParsingBio(false);
    }
  };

  const handleAddAllExtracted = async () => {
    for (const skill of extractedSkills) {
      await handleAddSkill(skill);
    }
    setExtractedSkills([]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Student Profile & Skill Inventory
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Keep your academic details and technical competencies current to power accurate AI matching and eligibility checks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Academic & Personal Form */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSaveProfile} className="glass-panel p-6 sm:p-7 rounded-3xl space-y-5">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-brand-400" />
              Academic Credentials
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Degree */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Degree</label>
                <select
                  value={formData.degree}
                  onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="B.Tech">B.Tech (Bachelor of Technology)</option>
                  <option value="B.E.">B.E. (Bachelor of Engineering)</option>
                  <option value="BCA">BCA (Computer Applications)</option>
                  <option value="M.Tech">M.Tech</option>
                  <option value="MCA">MCA</option>
                  <option value="B.Sc">B.Sc Computer Science</option>
                </select>
              </div>

              {/* Branch */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Branch / Discipline</label>
                <input
                  type="text"
                  value={formData.branch}
                  onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                  placeholder="e.g. Computer Science & Engineering"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                  required
                />
              </div>

              {/* Academic Year */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Academic Year</label>
                <select
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: Number(e.target.value) })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                >
                  <option value={1}>1st Year (Freshman)</option>
                  <option value={2}>2nd Year (Sophomore)</option>
                  <option value={3}>3rd Year (Pre-final)</option>
                  <option value={4}>4th Year (Final Year)</option>
                  <option value={5}>5th Year (Dual Degree)</option>
                </select>
              </div>

              {/* CGPA */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">CGPA (out of 10.0)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.0"
                  max="10.0"
                  value={formData.cgpa}
                  onChange={(e) => setFormData({ ...formData, cgpa: Number(e.target.value) })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              {/* Experience Level */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Technical Experience</label>
                <select
                  value={formData.experience_level}
                  onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="Beginner">Beginner (1-2 projects / coursework)</option>
                  <option value="Intermediate">Intermediate (Hackathon winner / internships)</option>
                  <option value="Advanced">Advanced (Production scale / open source)</option>
                </select>
              </div>

              {/* College Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">College / University</label>
                <input
                  type="text"
                  value={formData.college_name}
                  onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
                  placeholder="e.g. Indian Institute of Information Technology"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            {/* Raw Bio & NLP Skill Extraction */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Raw Bio / Resume Summary
                </label>
                <button
                  type="button"
                  onClick={handleExtractBioSkills}
                  disabled={parsingBio || !formData.raw_bio.trim()}
                  className="text-xs text-ai-primary hover:text-ai-glow font-semibold flex items-center gap-1 transition-colors disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{parsingBio ? 'Extracting...' : 'Extract Skills from Bio'}</span>
                </button>
              </div>

              <textarea
                rows={4}
                value={formData.raw_bio}
                onChange={(e) => setFormData({ ...formData, raw_bio: e.target.value })}
                placeholder="Paste your resume summary or technical bio here (e.g. 'I am a 3rd year student passionate about building scalable microservices with FastAPI and React, fine-tuning PyTorch models...')"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 leading-relaxed"
              />
            </div>

            {/* Extracted Skills Callout Box */}
            {extractedSkills.length > 0 && (
              <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/25 animate-in fade-in duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-ai-primary" />
                    Detected {extractedSkills.length} New Skills from Your Bio
                  </span>
                  <button
                    type="button"
                    onClick={handleAddAllExtracted}
                    className="text-xs font-bold px-2.5 py-1 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
                  >
                    Add All Detected
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {extractedSkills.map((sk, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleAddSkill(sk)}
                      className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-indigo-200 border border-indigo-500/30 flex items-center gap-1 transition-colors"
                    >
                      <Plus className="w-3 h-3 text-indigo-400" />
                      <span>{sk}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Social links */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Github className="w-3.5 h-3.5" />
                  GitHub URL
                </label>
                <input
                  type="url"
                  value={formData.github_url}
                  onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                  placeholder="https://github.com/username"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Linkedin className="w-3.5 h-3.5" />
                  LinkedIn URL
                </label>
                <input
                  type="url"
                  value={formData.linkedin_url}
                  onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            {/* Save Button */}
            <div className="pt-2 flex items-center justify-between">
              {saveSuccess && (
                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5 animate-in fade-in">
                  <Check className="w-4 h-4" />
                  Profile updated successfully!
                </span>
              )}
              <div className="ml-auto">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-brand-500/20 active:scale-95 transition-all"
                >
                  <Save className="w-4 h-4" />
                  <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Right Column: Skills Inventory Manager */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-indigo-400" />
                Skill Inventory
              </h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-brand-300 font-bold border border-slate-700">
                {profile.skills.length} Skills
              </span>
            </div>

            {/* Add Skill Form */}
            <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="Enter skill (e.g. Docker, PyTorch, React)"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-brand-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
              />

              <div className="grid grid-cols-2 gap-2">
                <select
                  value={newSkillLevel}
                  onChange={(e) => setNewSkillLevel(e.target.value)}
                  className="px-2 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                  <option value="Expert">Expert</option>
                </select>

                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  value={newSkillExp}
                  onChange={(e) => setNewSkillExp(Number(e.target.value))}
                  placeholder="Years"
                  className="px-2 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white text-center"
                />
              </div>

              <button
                type="button"
                onClick={() => handleAddSkill()}
                disabled={addingSkill || !newSkillName.trim()}
                className="w-full py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{addingSkill ? 'Adding...' : 'Add Skill'}</span>
              </button>
            </div>

            {/* Skills Chip List */}
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {profile.skills.length > 0 ? (
                profile.skills.map((s) => (
                  <div
                    key={s.skill_id || s.name}
                    className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-2 group hover:border-slate-700 transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-semibold text-white">{s.name}</span>
                        {s.verified && (
                          <span className="text-[10px] text-emerald-400 font-bold" title="Verified Skill">
                            ✓
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {s.proficiency_level} • {s.years_of_experience || 1.0} yrs
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDeleteSkill(s.skill_id)}
                      className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Remove skill"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-slate-500">
                  No skills attached yet. Add competencies above or extract from your bio.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
