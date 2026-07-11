<template>
  <template v-if="conseil">
    <p style="margin: 0"><router-link to="/conseils">← Tous les conseils</router-link></p>
    <h1>{{ titreCourt }}</h1>
    <p class="sous-titre">
      <template v-if="conseil.date_conseil">{{ formatDate(conseil.date_conseil) }} — </template>
      <a :href="conseil.url" target="_blank" rel="noopener">compte rendu officiel →</a>
    </p>

    <section v-if="conseil.decisions.length">
      <h2>Décisions ({{ conseil.decisions.length }})</h2>
      <div class="liste">
        <article v-for="d in conseil.decisions" :key="d.id" class="item">
          <div class="meta">
            <span class="badge">{{ LIBELLES_DECISION[d.type] ?? d.type }}</span>
            <span v-if="d.ministere">{{ d.ministere }}</span>
          </div>
          <div class="detail">{{ d.objet }}</div>
        </article>
      </div>
    </section>

    <section v-if="conseil.engagements.length" style="margin-top: 24px">
      <h2>Engagements financiers ({{ conseil.engagements.length }})</h2>
      <div class="liste">
        <article v-for="e in conseil.engagements" :key="e.id" class="item">
          <div class="meta"><span class="badge">{{ LIBELLES_ENGAGEMENT[e.type] ?? e.type }}</span></div>
          <div class="titre">
            {{ fmtFCFA(e.montant_fcfa) }}<template v-if="e.beneficiaire"> — {{ e.beneficiaire }}</template>
          </div>
          <div class="detail">{{ e.objet }}</div>
        </article>
      </div>
    </section>

    <section v-if="conseil.nominations.length" style="margin-top: 24px">
      <h2>Nominations ({{ conseil.nominations.length }})</h2>
      <div class="liste">
        <article v-for="n in conseil.nominations" :key="n.id" class="item">
          <div class="meta">
            <span class="badge">{{ n.type === "fin_fonction" ? "Fin de fonction" : "Nomination" }}</span>
          </div>
          <div class="titre">{{ n.personne }}</div>
          <div class="detail">{{ n.poste }}<template v-if="n.structure"> — {{ n.structure }}</template></div>
        </article>
      </div>
    </section>
  </template>
  <p v-else class="chargement">Chargement…</p>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { apiGet } from "../api";

const LIBELLES_DECISION = {
  adoption_decret: "Décret",
  adoption_loi: "Projet de loi",
  rapport: "Rapport",
  communication: "Communication",
  autorisation: "Autorisation",
  autre: "Autre",
};
const LIBELLES_ENGAGEMENT = {
  marche: "Marché public",
  convention: "Convention",
  pret: "Prêt",
  subvention: "Subvention",
  garantie: "Garantie",
  decaissement: "Décaissement",
  autre: "Autre",
};

const route = useRoute();
const conseil = ref(null);

const titreCourt = computed(() =>
  (conseil.value?.titre || "Conseil des ministres").replace(
    /^CONSEIL DES MINISTRES\s*/i,
    "Conseil des ministres ",
  ),
);

function formatDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
function fmtFCFA(n) {
  if (n == null) return "—";
  if (n >= 1e9) return `${(n / 1e9).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} Mds FCFA`;
  if (n >= 1e6) return `${(n / 1e6).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} M FCFA`;
  return `${n.toLocaleString("fr-FR")} FCFA`;
}

onMounted(async () => {
  conseil.value = await apiGet(`/conseils/${route.params.id}`);
});
</script>
