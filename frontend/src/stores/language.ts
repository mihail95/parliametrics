import { defineStore } from 'pinia'

export const useLanguageStore = defineStore('language', {
  state: () => ({
    lang: 'bg' as 'bg' | 'en'
  }),
  actions: {
    setLang(newLang: 'bg' | 'en') {
      this.lang = newLang
    }
  }
})