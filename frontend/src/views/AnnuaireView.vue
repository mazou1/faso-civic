<template>
  <h1>Annuaire de l'État</h1>
  <p class="sous-titre">
    Qui occupe quel poste, dans quelle structure, depuis quand — reconstitué à partir des
    nominations officielles en Conseil des ministres.
  </p>

  <nav class="onglets">
    <router-link to="/annuaire" class="actif">Annuaire</router-link>
    <router-link to="/annuaire/nominations">Nominations</router-link>
  </nav>

  <div class="filtres entete-recherche">
    <input
      v-model="q"
      type="search"
      placeholder="Personne, structure, sigle ou poste…"
      @input="rechercherDebounce"
    />
    <label style="display: flex; align-items: center; gap: 6px">
      <input v-model="enCours" type="checkbox" @change="page = 1; recharger()" />
      En cours uniquement
    </label>
    <span class="compteur" v-if="total !== null">{{ total.toLocaleString("fr-FR") }} mandats</span>
  </div>

  <div class="grille-mandats">
    <article v-for="m in mandats" :key="m.id" class="carte mandat" :class="{ termine: m.date_fin }">
      <div class="avatar">{{ initiales(m.personne) }}</div>
      <div class="corps">
        <div class="entete-mandat">
          <router-link class="nom" :to="`/personnes/${m.personne_id}`">{{ m.personne }}</router-link>
          <span class="badge">{{ m.date_fin ? "Terminé" : "En cours" }}</span>
          <span class="matricule" v-if="m.matricule">Mle {{ m.matricule }}</span>
        </div>
        <div class="poste">{{ m.poste }}<template v-if="m.structure"> — {{ m.structure }}</template></div>
        <div class="dates">
          <template v-if="m.date_debut">Depuis le {{ formatDate(m.date_debut) }}</template>
          <template v-if="m.date_fin"> → {{ formatDate(m.date_fin) }}</template>
          <a v-if="m.document_url" :href="m.document_url" target="_blank" rel="noopener"> · compte rendu →</a>
        </div>
      </div>
    </article>
  </div>

  <p v-if="chargement" class="chargement">Chargement…</p>
  <p v-else-if="!mandats.length" class="vide">Aucun mandat trouvé.</p>

  <div class="pagination">
    <button :disabled="page <= 1" @click="page--; recharger()">← Précédent</button>
    <span>Page {{ page }}<template v-if="pages"> / {{ pages }}</template></span>
    <button :disabled="page >= pages" @click="page++; recharger()">Suivant →</button>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiGet } from "../api";

const PAR_PAGE = 24;
const mandats = ref([]);
const total = ref(null);
const q = ref("");
const enCours = ref(false);
const page = ref(1);
const chargement = ref(false);
let minuterie = null;

const pages = computed(() => (total.value ? Math.ceil(total.value / PAR_PAGE) : 0));

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}
function initiales(nom) {
  return nom
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();
}

async function recharger() {
  chargement.value = true;
  try {
    const r = await apiGet("/annuaire", {
      q: q.value.length >= 2 ? q.value : undefined,
      en_cours: enCours.value ? "true" : undefined,
      page: page.value,
      par_page: PAR_PAGE,
    });
    mandats.value = r.mandats;
    total.value = r.total;
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

<style scoped>
.entete-recherche { align-items: center; }
.entete-recherche input[type="search"] { flex: 1; max-width: 420px; }
.compteur { margin-left: auto; color: var(--text-muted); font-size: 0.88rem; }

.grille-mandats { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 12px; }
.mandat { display: flex; gap: 14px; align-items: flex-start; padding: 14px 16px; }
.mandat.termine { opacity: 0.72; }
.avatar {
  flex: none; width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  color: var(--accent); font-weight: 700;
}
.corps { min-width: 0; }
.entete-mandat { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.entete-mandat .nom { font-weight: 700; color: inherit; text-decoration: none; }
.entete-mandat .nom:hover { color: var(--accent); }
.entete-mandat .matricule { color: var(--text-muted); font-size: 0.78rem; }
.poste { color: var(--text-secondary); font-size: 0.92rem; margin-top: 2px; }
.dates { color: var(--text-muted); font-size: 0.82rem; margin-top: 6px; }
</style>
