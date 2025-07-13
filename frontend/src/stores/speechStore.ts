import { defineStore } from 'pinia'
import type { Speech, FilterOptions } from '@/interfaces/speech'

export const useSpeechStore = defineStore('speech', {
    state: () => ({
        filters: null as FilterOptions | null,
        speeches: [] as Speech[],
        fetched: false,
        selectedSpeakers: [] as number[],
        selectedParties: [] as number[],
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
            const url = new URL('http://localhost:8000/speeches')
            const params = new URLSearchParams()

            params.set('skip', ((this.page - 1) * limit).toString())
            params.set('limit', limit.toString())

            // Add speaker_ids as multiple query params
            if (this.selectedSpeakers.length > 0) {
                this.selectedSpeakers.forEach(id => params.append('speaker_ids', id.toString()))
            }

            // Add party_ids as multiple query params
            if (this.selectedParties.length > 0) {
                this.selectedParties.forEach(id => params.append('party_ids', id.toString()))
            }

            if (this.selectedLocation !== null) {
                params.set('from_tribune', this.selectedLocation.toString())
            }
            if (this.dateFrom) params.set('date_from', this.dateFrom)
            if (this.dateTo) params.set('date_to', this.dateTo)

            url.search = params.toString()

            const res = await fetch(url.toString())
            if (!res.ok) throw new Error('Failed to fetch speeches')
            this.speeches = await res.json()
            this.fetched = true
        }
    }
})
