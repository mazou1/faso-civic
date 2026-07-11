<template>
  <h1>L'Assemblée législative</h1>
  <p class="sous-titre">
    Composition de l'Assemblée législative du Peuple, synchronisée depuis le
    <a href="https://www.assembleenationale.bf" target="_blank" rel="noopener">site officiel</a> —
    et les lois adoptées, issues de Légiburkina.
  </p>

  <div v-if="data" class="grille-tuiles">
    <div class="carte tuile">
      <div class="valeur">{{ data.stats.deputes }}</div>
      <div class="libelle">députés</div>
    </div>
    <div class="carte tuile" v-if="data.stats.legislature">
      <div class="valeur">{{ data.stats.legislature }}</div>
      <div class="libelle">législature</div>
    </div>
  </div>

  <h2>Dernières lois adoptées</h2>
  <div class="liste" style="margin-bottom: 28px">
    <article v-for="t in lois" :key="t.id" class="item">
      <div class="meta">
        <span class="badge">Loi</span>
        <span v-if="t.date_publication">{{ formatDate(t.date_publication) }}</span>
        <span v-if="t.secteur">{{ t.secteur }}</span>
      </div>
      <div class="titre">{{ t.reference ? `N° ${t.reference.replace(/^N°\s*/, "")}` : t.titre }}</div>
      <div v-if="t.description" class="detail">{{ t.description }}</div>
      <a class="source" :href="t.url_pdf" target="_blank" rel="noopener">Texte intégral (PDF) →</a>
    </article>
  </div>
  <p><router-link to="/textes">Toutes les lois et décrets →</router-link></p>

  <h2 style="margin-top: 24px">Les députés</h2>
  <div class="filtres">
    <input v-model="q" type="search" placeholder="Rechercher un député…" />
  </div>
  <div v-if="data" class="grille-deputes">
    <article v-for="d in deputesFiltres" :key="d.nom_complet" class="carte depute">
      <img
        v-if="d.photo_url"
        :src="d.photo_url"
        :alt="d.nom_complet"
        loading="lazy"
        @error="(e) => (e.target.style.display = 'none')"
      />
      <div class="detail">{{ d.nom_complet }}</div>
    </article>
  </div>
  <p v-else class="chargement">Chargement…</p>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiGet } from "../api";

const data = ref(null);
const lois = ref([]);
const q = ref("");

const deputesFiltres = computed(() => {
  const motif = q.value.trim().toLowerCase();
  const tous = data.value?.deputes ?? [];
  return motif ? tous.filter((d) => d.nom_complet.toLowerCase().includes(motif)) : tous;
});

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

onMounted(async () => {
  [data.value, lois.value] = await Promise.all([
    apiGet("/assemblee"),
    apiGet("/textes", { type: "loi", par_page: 5 }),
  ]);
});
</script>

<style scoped>
.grille-deputes { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.depute { text-align: center; padding: 12px; }
.depute img { width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 8px; }
</style>
