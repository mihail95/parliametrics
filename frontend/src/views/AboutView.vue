<template>
  <div class="container py-4">
    <h2 class="mb-4">{{ t('about_title') }}</h2>

    <div class="row mb-4">
      <div class="col-12 col-md-8">
        <p>{{ t('about_intro') }}</p>
        <p>{{ t('about_goal') }}</p>
        <p>{{ t('about_features') }}</p>
        <p>{{ t('about_dataset') }}</p>
        <p>{{ t('about_future') }}</p>
      </div>
    </div>

    <h4 class="mb-3">{{ t('project_info') }}</h4>
    <div class="row">
      <div class="col-12 col-md-6 mb-3">
        <strong>{{ t('author') }}:</strong><br />
        Mihail Chifligarov
      </div>
      <div class="col-12 col-md-6 mb-3">
        <strong>{{ t('contact') }}:</strong><br />
        mihail.chifligarov@ruhr-uni-bochum.de
      </div>
      <div class="col-12 col-md-6 mb-3">
        <strong>{{ t('frontend') }}:</strong><br />
        Vue 3 + Vite + TypeScript + Bootstrap 5
      </div>
      <div class="col-12 col-md-6 mb-3">
        <strong>{{ t('backend') }}:</strong><br />
        FastAPI + PostgreSQL + SQLAlchemy
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTranslate } from '@/composables/useTranslate'
const t = useTranslate()
</script>

<style scoped>
h2 {
  font-size: 2rem;
  font-weight: 600;
}
</style>
