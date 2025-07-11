import { defineStore } from 'pinia'
import type { Speech, FilterOptions } from '@/interfaces/speech'

export const useSpeechStore = defineStore('speech', {
    state: () => ({
        filters: null as FilterOptions | null,
        speeches: [] as Speech[],
        fetched: false,
        selectedSpeaker: null as number | null,
        selectedParty: null as number | null,
        selectedLocation: null as boolean | null,
        dateFrom: null as string | null,
        dateTo: null as string | null,
        page: 1
    }),
    actions: {
        async fetchFilters() {
            const res = await fetch('http://localhost:8000/speeches/filters')
            if (!res.ok) throw new Error('Failed to fetch filters')
            this.filters = await res.json()

            if (this.filters && !this.dateFrom && this.filters.dates.length > 0) {
                this.dateFrom = this.filters.dates[0]
            }
            if (this.filters && !this.dateTo && this.filters.dates.length > 0) {
                this.dateTo = this.filters.dates[this.filters.dates.length - 1]
            }
        },
        async fetchSpeeches(limit = 20) {
            const params: Record<string, string> = {
                skip: ((this.page - 1) * limit).toString(),
                limit: limit.toString()
            }
            if (this.selectedSpeaker !== null) params.speaker_id = this.selectedSpeaker.toString()
            if (this.selectedParty !== null) params.party_id = this.selectedParty.toString()
            if (this.selectedLocation !== null) params.from_tribune = this.selectedLocation.toString()
            if (this.dateFrom) params.date_from = this.dateFrom
            if (this.dateTo) params.date_to = this.dateTo

            const url = new URL('http://localhost:8000/speeches')
            url.search = new URLSearchParams(params).toString()
            const res = await fetch(url.toString())
            if (!res.ok) throw new Error('Failed to fetch speeches')
            this.speeches = await res.json()
            this.fetched = true
        }
    }
})
