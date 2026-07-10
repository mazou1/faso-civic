<template>
  <h1>Lois & décrets</h1>
  <p class="sous-titre">
    Le droit burkinabè publié : décrets, lois, arrêtés et autres textes, avec leur PDF officiel
    et le Journal officiel de publication.
  </p>

  <div class="filtres">
    <input
      v-model="q"
      type="search"
      placeholder="Rechercher (ex : mine d'or, éducation, état d'urgence…)"
      @input="rechercherDebounce"
    />
    <select v-model="type" @change="page = 1; recharger()">
      <option value="">Tous les textes</option>
      <option value="decret">Décrets</option>
      <option value="loi">Lois</option>
      <option value="arrete">Arrêtés</option>
      <option value="ordonnance">Ordonnances</option>
      <option value="charte">Chartes</option>
      <option value="constitution">Constitution</option>
    </select>
  </div>

  <div class="liste">
    <article v-for="t in textes" :key="t.id" class="item">
      <div class="meta">
        <span class="badge">{{ LIBELLES[t.type_doc] ?? t.type_doc }}</span>
        <span v-if="t.date_publication">{{ formatDate(t.date_publication) }}</span>
        <span v-if="t.secteur">{{ t.secteur }}</span>
      </div>
      <div class="titre">{{ t.reference ? `N° ${t.reference.replace(/^N°\s*/, "")}` : t.titre }}</div>
      <div v-if="t.description" class="detail">{{ majuscule(t.description) }}</div>
      <div class="meta" style="margin-top: 6px">
        <a class="source" :href="t.url_pdf" target="_blank" rel="noopener">Texte intégral (PDF) →</a>
        <a v-if="t.jo_url" class="source" :href="t.jo_url" target="_blank" rel="noopener">
          Journal officiel {{ t.jo_numero }} →
        </a>
      </div>
    </article>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!textes.length" class="vide">Aucun texte ne correspond à cette recherche.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}</span>
    <button :disabled="textes.length < PAR_PAGE" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { apiGet } from "../api";

const LIBELLES = {
  decret: "Décret",
  loi: "Loi",
  arrete: "Arrêté",
  ordonnance: "Ordonnance",
  charte: "Charte",
  constitution: "Constitution",
  texte_juridique: "Texte",
};
const PAR_PAGE = 20;

const textes = ref([]);
const q = ref("");
const type = ref("");
const page = ref(1);
const chargement = ref(false);
let minuterie = null;

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}
function majuscule(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

async function recharger() {
  chargement.value = true;
  try {
    textes.value = await apiGet("/textes", {
      q: q.value.length >= 2 ? q.value : undefined,
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
