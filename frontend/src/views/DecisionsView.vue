<template>
  <h1>Décisions du Conseil des ministres</h1>
  <p class="sous-titre">Chaque décision renvoie au compte rendu officiel dont elle est extraite.</p>

  <div class="filtres">
    <input
      v-model="ministere"
      type="search"
      placeholder="Filtrer par ministère (ex : justice, énergie…)"
      @input="rechercherDebounce"
    />
    <select v-model="type" @change="recharger">
      <option value="">Toutes natures</option>
      <option value="adoption_decret">Décrets adoptés</option>
      <option value="adoption_loi">Projets de loi</option>
      <option value="rapport">Rapports</option>
      <option value="communication">Communications</option>
      <option value="autorisation">Autorisations</option>
      <option value="autre">Autres</option>
    </select>
  </div>

  <div class="liste">
    <article v-for="d in decisions" :key="d.id" class="item">
      <div class="meta">
        <span class="badge">{{ LIBELLES[d.type] ?? d.type }}</span>
        <span v-if="d.date_conseil">Conseil du {{ formatDate(d.date_conseil) }}</span>
        <span v-if="d.ministere">{{ d.ministere }}</span>
      </div>
      <div class="detail">{{ d.objet }}</div>
      <a class="source" :href="d.document_url" target="_blank" rel="noopener">Voir le compte rendu officiel →</a>
    </article>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!decisions.length" class="vide">Aucune décision ne correspond à ces filtres.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}</span>
    <button :disabled="decisions.length < PAR_PAGE" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiGet } from "../api";

const LIBELLES = {
  adoption_decret: "Décret",
  adoption_loi: "Projet de loi",
  rapport: "Rapport",
  communication: "Communication",
  autorisation: "Autorisation",
  autre: "Autre",
};
const PAR_PAGE = 20;

const decisions = ref([]);
const ministere = ref("");
const type = ref("");
const page = ref(1);
const chargement = ref(false);
let minuterie = null;

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

async function recharger() {
  chargement.value = true;
  try {
    decisions.value = await apiGet("/decisions", {
      ministere: ministere.value,
      type: type.value,
      page: page.value,
      par_page: PAR_PAGE,
    });
  } finally {
    chargement.value = false;
  }
}

function rechercherDebounce() {
  clearTimeout(minuterie);
  minuterie = setTimeout(() => {
    page.value = 1;
    recharger();
  }, 350);
}

onMounted(recharger);
</script>
