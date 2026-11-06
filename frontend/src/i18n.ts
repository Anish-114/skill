import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import hiLatn from './locales/hi-Latn.json';

export const LANGUAGE_STORAGE_KEY = 'skillbridge_lang';
const savedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY) || 'en';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      'hi-Latn': { translation: hiLatn },
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

i18n.on('languageChanged', (lng) => {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, lng);
});

export default i18n;
