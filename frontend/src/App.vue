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
</script>

<template>
  <!-- Bootstrap navbar -->
  <nav class="navbar navbar-expand-lg navbar-light bg-light fixed-top">
    <div class="container-fluid">
      <!-- Brand on the left -->
      <RouterLink to="/" class="navbar-brand me-4" @click="collapseNavbar">Parliametrics</RouterLink>

      <!-- Toggler -->
      <button
        class="navbar-toggler"
        type="button"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
        @click="collapseNavbar"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- Collapsible nav content -->
      <div class="collapse navbar-collapse" id="navbarNav">
        <!-- Left-side nav links -->
        <ul class="navbar-nav me-auto mt-2 mt-lg-0">
          <li class="nav-item mx-2">
            <RouterLink to="/" class="nav-link" active-class="active" @click="collapseNavbar" exact>Home</RouterLink>
          </li>
          <li class="nav-item mx-2">
            <RouterLink to="/speeches" class="nav-link" active-class="active" @click="collapseNavbar">Speeches</RouterLink>
          </li>
          <li class="nav-item mx-2">
            <RouterLink to="/about" class="nav-link" active-class="active" @click="collapseNavbar">About</RouterLink>
          </li>
        </ul>
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
