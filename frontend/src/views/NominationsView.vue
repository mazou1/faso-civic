<template>
  <h1>Nominations officielles</h1>
  <p class="sous-titre">
    Personnes nommées en Conseil des ministres, avec poste, structure et lien vers le compte rendu.
  </p>

  <div class="filtres">
    <input
      v-model="q"
      type="search"
      placeholder="Rechercher une personne (ex : SABO, OUEDRAOGO…)"
      @input="rechercherDebounce"
    />
  </div>

  <div class="liste">
    <article v-for="n in nominations" :key="n.id" class="item">
      <div class="meta">
        <span class="badge">{{ n.type === "fin_fonction" ? "Fin de fonction" : "Nomination" }}</span>
        <span v-if="n.date_conseil">Conseil du {{ formatDate(n.date_conseil) }}</span>
      </div>
      <div class="titre">{{ n.personne }}</div>
      <div class="detail">
        {{ n.poste }}<template v-if="n.structure"> — {{ n.structure }}</template>
      </div>
      <a class="source" :href="n.document_url" target="_blank" rel="noopener">Voir le compte rendu officiel →</a>
    </article>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!nominations.length" class="vide">Aucune nomination trouvée.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}</span>
    <button :disabled="nominations.length < PAR_PAGE" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiGet } from "../api";

const PAR_PAGE = 20;
const nominations = ref([]);
const q = ref("");
const page = ref(1);
const chargement = ref(false);
let minuterie = null;

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

async function recharger() {
  chargement.value = true;
  try {
    nominations.value = await apiGet("/nominations", { q: q.value, page: page.value, par_page: PAR_PAGE });
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
