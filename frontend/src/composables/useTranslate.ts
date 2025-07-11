import { useLanguageStore } from '@/stores/language'
import { translations } from '@/i18n'

export function useTranslate() {
  const langStore = useLanguageStore()
  return (key: keyof typeof translations) => {
    return translations[key]?.[langStore.lang] ?? key
  }
}