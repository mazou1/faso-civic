<template>
  <h1>Conseils des ministres</h1>
  <p class="sous-titre">
    Chaque conseil, avec ce qui y a été décidé : délibérations, nominations et engagements financiers.
  </p>

  <div class="liste">
    <router-link
      v-for="c in conseils"
      :key="c.id"
      :to="`/conseils/${c.id}`"
      class="item item-lien"
    >
      <div class="meta">
        <span v-if="c.date_conseil" class="badge">{{ formatDate(c.date_conseil) }}</span>
      </div>
      <div class="titre">{{ titreCourt(c) }}</div>
      <div class="detail">
        {{ c.decisions }} décision{{ c.decisions > 1 ? "s" : "" }} ·
        {{ c.nominations }} nomination{{ c.nominations > 1 ? "s" : "" }}
        <template v-if="c.engagements"> · {{ c.engagements }} engagement{{ c.engagements > 1 ? "s" : "" }} financier{{ c.engagements > 1 ? "s" : "" }}</template>
      </div>
    </router-link>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!conseils.length" class="vide">Aucun conseil à afficher.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}</span>
    <button :disabled="conseils.length < PAR_PAGE" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiGet } from "../api";

const PAR_PAGE = 20;
const conseils = ref([]);
const page = ref(1);
const chargement = ref(false);

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}
function titreCourt(c) {
  return (c.titre || "Conseil des ministres").replace(/^CONSEIL DES MINISTRES\s*/i, "Conseil des ministres ");
}

async function recharger() {
  chargement.value = true;
  try {
    conseils.value = await apiGet("/conseils", { page: page.value, par_page: PAR_PAGE });
  } finally {
    chargement.value = false;
  }
}

onMounted(recharger);
</script>
