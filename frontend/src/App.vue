<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
// @ts-ignore
import Collapse from 'bootstrap/js/dist/collapse'

function collapseNavbar() {
  const el = document.getElementById('navbarNav')
  const toggler = document.querySelector('.navbar-toggler')

  // Only toggle if toggler is visible (i.e. mobile)
  if (toggler && window.getComputedStyle(toggler).display !== 'none') {
    const instance = Collapse.getOrCreateInstance(el)
    instance.toggle()
  }
}

import { useLanguageStore } from '@/stores/language'
import { useTranslate } from '@/composables/useTranslate'

const langStore = useLanguageStore()
const t = useTranslate()

</script>

<template>
  <!-- Bootstrap navbar -->
  <nav class="navbar navbar-expand-lg navbar-light bg-light fixed-top shadow-sm">
    <div class="container-fluid">
      <!-- Brand -->
      <RouterLink class="navbar-brand" to="/" @click="collapseNavbar">Parliametrics</RouterLink>

      <!-- Language selector (ALWAYS visible) -->
      <div class="d-lg-none ms-auto me-2">
        <select v-model="langStore.lang" class="form-select form-select-sm">
          <option value="bg">Български</option>
          <option value="en">English</option>
        </select>
      </div>

      <!-- Toggler -->
      <button
        class="navbar-toggler"
        type="button"
        @click="collapseNavbar"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- Collapse nav content -->
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item me-3">
            <RouterLink to="/" class="nav-link" active-class="active" exact @click="collapseNavbar">
              {{ t('home') }}
            </RouterLink>
          </li>
          <li class="nav-item me-3">
            <RouterLink to="/speeches" class="nav-link" active-class="active" @click="collapseNavbar">
              {{ t('speeches') }}
            </RouterLink>
          </li>
          <li class="nav-item me-3">
            <RouterLink to="/about" class="nav-link" active-class="active" @click="collapseNavbar">
              {{ t('about') }}
            </RouterLink>
          </li>
        </ul>

        <!-- Right-aligned language selector for desktop -->
        <div class="d-none d-lg-block ms-auto">
          <select v-model="langStore.lang" class="form-select form-select-sm w-auto">
            <option value="bg">Български</option>
            <option value="en">English</option>
          </select>
        </div>
      </div>
    </div>
  </nav>

  <!-- Main content under fixed navbar -->
  <div class="container pt-4">
    <RouterView />
  </div>
</template>

<style scoped>
.nav-link.active {
  font-weight: bold;
}
</style>
