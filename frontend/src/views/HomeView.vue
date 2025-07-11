<script setup lang="ts">
import { useTranslate } from '@/composables/useTranslate'
import { RouterLink } from 'vue-router'

const t = useTranslate()
</script>

<template>
  <main>
    <!-- Hero Section -->
    <section class="text-white text-center d-flex align-items-center justify-content-center hero-section">
      <div>
        <h1 class="display-3 fw-bold text-shadow hero-text">Parliametrics</h1>
        <p class="lead text-shadow mt-3 hero-text">
          {{ t('hero_subtitle_line_1') }}<br />
          {{ t('hero_subtitle_line_2') }}
        </p>
        <RouterLink to="/speeches" class="btn btn-primary btn-lg mt-4 hero-text">
          {{ t('browse_speeches') }}
        </RouterLink>
      </div>
    </section>

    <!-- Why Section -->
    <div class="container my-5">
      <h2>{{ t('why_heading') }}</h2>
      <p>{{ t('why_paragraph_1') }}</p>
      <p>{{ t('why_paragraph_2') }}</p>
    </div>

    <!-- What You Can Do -->
    <div class="container my-5">
      <h2 class="mb-4">{{ t('what_heading') }}</h2>
      <div class="row g-4">
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">{{ t('search_title') }}</h5>
              <p class="card-text">{{ t('search_text') }}</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">{{ t('filter_title') }}</h5>
              <p class="card-text">{{ t('filter_text') }}</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">{{ t('linguistic_title') }}</h5>
              <p class="card-text">{{ t('linguistic_text') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="text-center my-5">
      <h3>{{ t('cta_heading') }}</h3>
      <RouterLink to="/speeches" class="btn btn-success btn-lg mt-3">
        {{ t('cta_button') }}
      </RouterLink>
    </div>

    <!-- Footer -->
    <footer class="text-center text-muted small py-4">
      <p>
        <span v-html="t('footer_credits')"></span>
        <a href="https://github.com/mihail95/parliametrics" target="_blank">
          {{ t('footer_github') }}
        </a>
      </p>
    </footer>
  </main>
</template>

<style>
.hero-section {
  position: relative;
  background: url('https://upload.wikimedia.org/wikipedia/commons/5/5b/National_Assembly_of_Bulgaria_Sofia_TB.jpg') center center / cover no-repeat;
  min-height: 85vh;
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  z-index: 0;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 1;
}

.hero-text {
  position: relative;
  z-index: 2;
}
.text-shadow {
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
}
</style>
