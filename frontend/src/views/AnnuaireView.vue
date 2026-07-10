<template>
  <h1>Annuaire de l'État</h1>
  <p class="sous-titre">
    Mandats reconstitués à partir des nominations validées : qui occupe quel poste, dans quelle structure, depuis quand.
  </p>

  <div class="filtres">
    <input
      v-model="q"
      type="search"
      placeholder="Personne, structure, sigle ou poste…"
      @input="rechercherDebounce"
    />
    <label style="display: flex; align-items: center; gap: 6px">
      <input v-model="enCours" type="checkbox" @change="recharger" />
      Mandats en cours uniquement
    </label>
  </div>

  <div class="liste">
    <article v-for="m in mandats" :key="m.id" class="item">
      <div class="meta">
        <span class="badge">{{ m.date_fin ? "Terminé" : "En cours" }}</span>
        <span v-if="m.date_debut">Depuis le {{ formatDate(m.date_debut) }}</span>
        <span v-if="m.date_fin">→ {{ formatDate(m.date_fin) }}</span>
      </div>
      <div class="titre">{{ m.personne }}</div>
      <div class="detail">
        {{ m.poste }}<template v-if="m.structure"> — {{ m.structure }}</template>
      </div>
      <a v-if="m.document_url" class="source" :href="m.document_url" target="_blank" rel="noopener">
        Nomination au compte rendu officiel →
      </a>
    </article>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!mandats.length" class="vide">Aucun mandat trouvé.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}</span>
    <button :disabled="mandats.length < PAR_PAGE" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiGet } from "../api";

const PAR_PAGE = 25;
const mandats = ref([]);
const q = ref("");
const enCours = ref(false);
const page = ref(1);
const chargement = ref(false);
let minuterie = null;

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

async function recharger() {
  chargement.value = true;
  try {
    mandats.value = await apiGet("/annuaire", {
      q: q.value.length >= 2 ? q.value : undefined,
      en_cours: enCours.value ? "true" : undefined,
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
