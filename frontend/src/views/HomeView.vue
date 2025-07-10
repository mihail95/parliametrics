<script setup lang="ts">

</script>

<template>
  <main>
    <section class="text-white text-center d-flex align-items-center justify-content-center hero-section">
      <div>
        <h1 class="display-3 fw-bold text-shadow hero-text">Parliametrics</h1>
        <p class="lead text-shadow mt-3 hero-text">
          Explore and analyze speeches from the Bulgarian National Assembly —<br />
          transparently, interactively, and freely.
        </p>
        <RouterLink to="/speeches" class="btn btn-primary btn-lg mt-4 hero-text">Browse Speeches</RouterLink>
      </div>
    </section>
    <div class="container my-5">
      <h2>Why Parliametrics?</h2>
      <p>
        Parliamentary debates shape laws, reflect political values, and influence public perception. Yet access to these
        speeches — especially with analysis tools — has remained fragmented or opaque.
      </p>
      <p>
        Parliametrics aims to democratize access to Bulgaria’s parliamentary speech data and enable exploration through
        search, filters, and linguistic insights.
      </p>
    </div>
    <div class="container my-5">
      <h2 class="mb-4">What You Can Do</h2>
      <div class="row g-4">
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Search Speeches</h5>
              <p class="card-text">Find speeches by date, speaker, or context — or use advanced full-text and semantic
                search (coming soon).</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Filter by Metadata</h5>
              <p class="card-text">Explore speeches based on party affiliation, tribune presence, or time period.</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Linguistic Insights</h5>
              <p class="card-text">See lexical richness, token counts, and other language metrics per speech.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="text-center my-5">
      <h3>Ready to explore political discourse?</h3>
      <RouterLink to="/speeches" class="btn btn-success btn-lg mt-3">Start Browsing</RouterLink>
    </div>
    <footer class="text-center text-muted small py-4">
      <p>
        Built by Mihail Chifligarov · Data from Bulgarian Parliament API ·
        <a href="https://github.com/mihail95/parliametrics" target="_blank">View on GitHub</a>
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
  background-color: rgba(0, 0, 0, 0.4); /* adjust opacity here */
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