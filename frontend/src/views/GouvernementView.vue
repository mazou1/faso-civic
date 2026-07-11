<template>
  <h1>Le Gouvernement</h1>
  <p class="sous-titre" v-if="data">
    Composition officielle issue du
    <a :href="data.decret.url" target="_blank" rel="noopener">décret portant composition du Gouvernement</a>
    <template v-if="data.decret.date"> du {{ formatDate(data.decret.date) }}</template>.
  </p>

  <div v-if="data" class="grille-tuiles">
    <div class="carte tuile">
      <div class="valeur">{{ data.stats.membres }}</div>
      <div class="libelle">membres du gouvernement</div>
    </div>
    <div class="carte tuile">
      <div class="valeur">{{ data.stats.femmes }}</div>
      <div class="libelle">femmes ({{ pct(data.stats.femmes, data.stats.membres) }})</div>
    </div>
    <div class="carte tuile">
      <div class="valeur">{{ militaires }}</div>
      <div class="libelle">officiers ({{ pct(militaires, data.stats.membres) }})</div>
    </div>
  </div>

  <div v-if="data" class="grille-membres">
    <article v-for="m in data.membres" :key="m.ordre" class="carte membre" :class="{ pm: m.ordre === 0 }">
      <div class="avatar">{{ initiales(m.nom_complet) }}</div>
      <div>
        <div class="titre">{{ m.nom_complet }}</div>
        <div class="detail">{{ m.civilite && !civil(m.civilite) ? m.civilite + " — " : "" }}{{ m.poste }}</div>
      </div>
    </article>
  </div>
  <p v-else class="chargement">Chargement…</p>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiGet } from "../api";

const data = ref(null);

const militaires = computed(
  () => (data.value?.membres ?? []).filter((m) => m.civilite && !civil(m.civilite)).length,
);

function civil(c) {
  return ["monsieur", "madame"].includes((c || "").trim().toLowerCase());
}
function pct(n, total) {
  return total ? `${Math.round((n / total) * 100)} %` : "—";
}
function initiales(nom) {
  return nom
    .split(/\s+/)
    .filter((p) => p[0] === p[0]?.toUpperCase())
    .slice(0, 2)
    .map((p) => p[0])
    .join("");
}
function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

onMounted(async () => {
  data.value = await apiGet("/gouvernement");
});
</script>

<style scoped>
.grille-membres { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.membre { display: flex; gap: 14px; align-items: center; }
.membre.pm { grid-column: 1 / -1; border-color: var(--accent); }
.avatar {
  flex: none; width: 46px; height: 46px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  color: var(--accent); font-weight: 700;
}
</style>
