<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useTranslate } from '@/composables/useTranslate'
import { translations } from '@/i18n'
import type { Speech } from '@/interfaces/speech'
import { useSpeechStore } from '@/stores/speechStore'

const t = useTranslate()
const store = useSpeechStore()

const filters = computed(() => store.filters ?? {
  speakers: [],
  parties: [],
  from_tribune_options: [],
  dates: []
})

const speeches = computed(() => store.speeches)

const selectedSpeakers = computed({
  get: () => store.selectedSpeakers,
  set: (val) => { store.selectedSpeakers = val }
})
const selectedParties = computed({
  get: () => store.selectedParties,
  set: (val) => { store.selectedParties = val }
})
const selectedLocation = computed({
  get: () => store.selectedLocation,
  set: (val) => { store.selectedLocation = val }
})
const dateFrom = computed({
  get: () => store.dateFrom,
  set: (val) => { store.dateFrom = val }
})
const dateTo = computed({
  get: () => store.dateTo,
  set: (val) => { store.dateTo = val }
})
const page = computed({
  get: () => store.page,
  set: (val) => { store.page = val }
})

const limit = 20
const selectedSpeech = ref<Speech | null>(null)
const showModal = ref(false)
const ready = ref(false)

const speakerSearch = ref('')
const filteredSpeakers = computed(() =>
  filters.value.speakers.filter(s =>
    s.name.toLowerCase().includes(speakerSearch.value.toLowerCase())
  )
)

const duplicateSpeakerNames = computed(() => {
  const nameCounts: Record<string, number> = {}
  filters.value.speakers.forEach(s => {
    nameCounts[s.name] = (nameCounts[s.name] || 0) + 1
  })
  return new Set(Object.entries(nameCounts).filter(([, count]) => count > 1).map(([name]) => name))
})

watch(page, () => {
  if (ready.value) store.fetchSpeeches()
})

onMounted(async () => {
  if (!store.filters) await store.fetchFilters()
  if (!store.fetched) await store.fetchSpeeches()
  ready.value = true
})

function getSpeechPreview(text: string, maxLength = 50): string {
  return text.length > maxLength ? text.slice(0, maxLength) + '…' : text
}
function openModal(speech: Speech) {
  selectedSpeech.value = speech
  showModal.value = true
}
function closeModal() {
  selectedSpeech.value = null
  showModal.value = false
}

const columns: { key: keyof Speech; label: keyof typeof translations; formatter?: (val: any) => string }[] = [
  { key: 'datestamp', label: 'date' },
  { key: 'speaker_name', label: 'speaker' },
  { key: 'party_name', label: 'party' },
  {
    key: 'from_tribune',
    label: 'location',
    formatter: (val: boolean) => t(val ? 'tribune' : 'place')
  }
]

function resetFilters() {
  store.selectedSpeakers = []
  store.selectedParties = []
  store.selectedLocation = null
  store.dateFrom = store.filters?.dates[0] ?? null
  store.dateTo = store.filters?.dates[store.filters?.dates.length - 1] ?? null
  store.page = 1
}

const hasActiveFilters = computed(() => {
  const hasSpeakers = selectedSpeakers.value.length > 0
  const hasParties = selectedParties.value.length > 0
  const hasLocation = selectedLocation.value !== null

  const defaultFrom = store.filters?.dates[0] ?? null
  const defaultTo = store.filters?.dates[store.filters?.dates.length - 1] ?? null
  const hasDateFrom = dateFrom.value !== defaultFrom
  const hasDateTo = dateTo.value !== defaultTo

  return hasSpeakers || hasParties || hasLocation || hasDateFrom || hasDateTo
})
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4">{{ t('title') }}</h2>

    <!-- Filters -->
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <label class="form-label">{{ t('speaker') }}</label>
        <div class="dropdown">
          <button class="form-select text-start" type="button" data-bs-toggle="dropdown" aria-expanded="false">
            {{ selectedSpeakers.length ? `${t('selected')}: ${selectedSpeakers.length}` : t('all') }}
          </button>
          <ul class="dropdown-menu w-100 p-2" style="max-height: 300px; overflow-y: auto;" @click.stop>
            <input type="text" class="form-control mb-2" v-model="speakerSearch" :placeholder="t('search') + '…'" />
            <li>
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="allSpeakers"
                  :checked="selectedSpeakers.length === 0" @change="selectedSpeakers = []" />
                <label class="form-check-label" for="allSpeakers">{{ t('all') }}</label>
              </div>
            </li>
            <li v-for="s in filteredSpeakers" :key="s.id">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" :id="'speaker_' + s.id" :value="s.id"
                  v-model="selectedSpeakers" />
                <label class="form-check-label" :for="'speaker_' + s.id">
                  {{ s.name }}
                  <template v-if="duplicateSpeakerNames.has(s.name) && s.middle_name">
                    {{ ' (' + s.middle_name + ')' }}
                  </template>
                </label>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div class="col-md-3">
        <label class="form-label">{{ t('party') }}</label>
        <div class="dropdown">
          <button class="form-select text-start" type="button" data-bs-toggle="dropdown" aria-expanded="false">
            {{ selectedParties.length ? `${t('selected')}: ${selectedParties.length}` : t('all') }}
          </button>
          <ul class="dropdown-menu w-100 p-2" style="max-height: 300px; overflow-y: auto;" @click.stop>
            <li>
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="allParties" :checked="selectedParties.length === 0"
                  @change="selectedParties = []" />
                <label class="form-check-label" for="allParties">{{ t('all') }}</label>
              </div>
            </li>
            <li v-for="p in filters.parties" :key="p.id">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" :id="'party_' + p.id" :value="p.id"
                  v-model="selectedParties" />
                <label class="form-check-label" :for="'party_' + p.id">
                  {{ p.name }} ({{ p.abbr }})
                </label>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div class="col-md-2">
        <label class="form-label" for="fromTribune">{{ t('from_tribune') }}</label>
        <select id="fromTribune" class="form-select" v-model="selectedLocation">
          <option :value="null">{{ t('all') }}</option>
          <option v-for="opt in filters.from_tribune_options" :key="String(opt)" :value="opt">
            {{ t(opt ? 'tribune_yes' : 'tribune_no') }}
          </option>
        </select>
      </div>

      <div class="col-md-2">
        <label class="form-label">{{ t('date_from') }}</label>
        <input type="date" class="form-control" v-model="dateFrom" :max="dateTo || undefined" />
      </div>

      <div class="col-md-2">
        <label class="form-label">{{ t('date_to') }}</label>
        <input type="date" class="form-control" v-model="dateTo" :min="dateFrom || undefined" />
      </div>

      <div class="text-end mb-3 d-flex justify-content-end gap-2">
        <div
          :title="!hasActiveFilters ? t('no_filters_to_clear') : undefined"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
        >
          <button
            class="btn"
            :class="hasActiveFilters ? 'btn-danger' : 'btn-secondary'"
            :disabled="!hasActiveFilters"
            @click="resetFilters"
          >
            {{ t('clear_filters') }}
          </button>
        </div>
        <button class="btn btn-primary" @click="store.fetchSpeeches()">
          {{ t('apply_filters') }}
        </button>
      </div>
    </div>

    <!-- Table view (md and up) -->
    <div class="table-responsive d-none d-md-block">
      <table class="table table-bordered table-striped align-middle">
        <thead class="table-light">
          <tr>
            <th v-for="col in columns" :key="col.key">{{ t(col.label) }}</th>
            <th>{{ t('view') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="speech in speeches" :key="speech.speech_id">
            <td v-for="col in columns" :key="col.key">
              {{ col.formatter ? col.formatter(speech[col.key]) : speech[col.key] }}
            </td>
            <td @click="openModal(speech)" class="text-primary fw-semibold"
              style="cursor: pointer; text-decoration: underline dotted;" :title="t('view')">
              {{ getSpeechPreview(speech.speech_content) }}
              <i class="bi bi-eye float-end"></i>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Card view (sm and below) -->
    <div class="d-block d-md-none">
      <div class="card mb-3" v-for="speech in speeches" :key="speech.speech_id">
        <div class="card-body">
          <p><strong>{{ t('date') }}:</strong> {{ speech.datestamp }}</p>
          <p><strong>{{ t('speaker') }}:</strong> {{ speech.speaker_name }}</p>
          <p><strong>{{ t('party') }}:</strong> {{ speech.party_name }}</p>
          <p><strong>{{ t('location') }}:</strong> {{ t(speech.from_tribune ? 'tribune' : 'place') }}</p>
          <p class="mt-2 text-primary fw-semibold" style="cursor: pointer; text-decoration: underline dotted;"
            @click="openModal(speech)">
            {{ getSpeechPreview(speech.speech_content) }}
            <i class="bi bi-eye float-end"></i>
          </p>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="d-flex justify-content-center mt-4">
      <button class="btn btn-outline-secondary me-2" :disabled="page === 1" @click="page--">
        {{ t('prev') }}
      </button>
      <span class="align-self-center">{{ t('page') }} {{ page }}</span>
      <button class="btn btn-outline-secondary ms-2" :disabled="speeches.length < limit" @click="page++">
        {{ t('next') }}
      </button>
    </div>

    <!-- Modal -->
    <div v-if="showModal && selectedSpeech" class="modal fade show d-block" tabindex="-1"
      style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('full_speech') }}</h5>
            <button type="button" class="btn-close" @click="closeModal()"></button>
          </div>
          <div class="modal-body">
            <p><strong>{{ t('speaker') }}:</strong> {{ selectedSpeech.speaker_name }}</p>
            <p><strong>{{ t('party') }}:</strong> {{ selectedSpeech.party_name }} - {{ selectedSpeech.party_abbreviation
              }}
            </p>
            <p><strong>{{ t('date') }}:</strong> {{ selectedSpeech.datestamp }}</p>
            <p><strong>{{ t('location') }}:</strong> {{ t(selectedSpeech.from_tribune ? 'tribune' : 'place') }}</p>
            <hr />
            <pre style="white-space: pre-wrap;">{{ selectedSpeech.speech_content }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal.fade.show {
  display: block;
}

.bi-eye {
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0.6;
}

.bi-eye:hover {
  transform: scale(1.2);
  opacity: 1;
  color: #0d6efd;
}
</style>
