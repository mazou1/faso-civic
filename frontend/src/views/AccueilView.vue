<template>
  <h1>L'activité gouvernementale, en clair</h1>
  <p class="sous-titre">
    Décisions du Conseil des ministres et nominations officielles du Burkina Faso,
    extraites des comptes rendus publics et reliées à leurs sources.
  </p>

  <div v-if="stats" class="grille-tuiles">
    <div class="carte tuile" v-for="t in tuiles" :key="t.libelle">
      <div class="valeur">{{ t.valeur.toLocaleString("fr-FR") }}</div>
      <div class="libelle">{{ t.libelle }}</div>
    </div>
  </div>

  <div class="grille-graphes">
    <div class="carte graphe-large">
      <h2>Décisions et nominations par année</h2>
      <div ref="elAnnees" class="graphe" style="height: 260px"></div>
    </div>
    <div class="carte">
      <h2>Décisions par nature</h2>
      <div ref="elTypes" class="graphe" style="height: 260px"></div>
    </div>
    <div class="carte">
      <h2>Structures les plus concernées par les nominations</h2>
      <div ref="elStructures" class="graphe" style="height: 260px"></div>
    </div>
  </div>
  <p v-if="!stats" class="chargement">Chargement…</p>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { apiGet } from "../api";
import { baseOptions, monter, roles } from "../charts";

const LIBELLES_TYPE = {
  adoption_decret: "Décrets adoptés",
  adoption_loi: "Projets de loi",
  rapport: "Rapports",
  communication: "Communications",
  autorisation: "Autorisations",
  autre: "Autres",
};

const stats = ref(null);
const elAnnees = ref(null);
const elTypes = ref(null);
const elStructures = ref(null);
const nettoyages = [];

const tuiles = computed(() => {
  const t = stats.value?.totaux ?? {};
  return [
    { libelle: "décisions", valeur: t.decisions ?? 0 },
    { libelle: "nominations", valeur: t.nominations ?? 0 },
    { libelle: "personnes nommées", valeur: t.personnes ?? 0 },
    { libelle: "comptes rendus couverts", valeur: t.comptes_rendus ?? 0 },
  ];
});

function barreH(c, categories, valeurs) {
  // Barres horizontales, une seule série : pas de boîte de légende (le titre nomme la série).
  return {
    ...baseOptions(c),
    xAxis: { type: "value", splitLine: { lineStyle: { color: c.grille } }, axisLabel: { color: c.texteSecondaire } },
    yAxis: {
      type: "category",
      data: categories,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: c.texte, width: 180, overflow: "truncate" },
    },
    series: [
      {
        type: "bar",
        data: valeurs,
        barWidth: 14,
        itemStyle: { color: c.serie1, borderRadius: [0, 4, 4, 0] },
      },
    ],
  };
}

onMounted(async () => {
  stats.value = await apiGet("/stats");
  const c = roles();
  const s = stats.value;

  nettoyages.push(
    monter(elAnnees.value, {
      ...baseOptions(c),
      legend: { top: 0, right: 0, textStyle: { color: c.texteSecondaire }, itemWidth: 14, itemHeight: 10 },
      xAxis: {
        type: "category",
        data: s.par_annee.map((a) => a.annee),
        axisLine: { lineStyle: { color: c.grille } },
        axisTick: { show: false },
        axisLabel: { color: c.texte },
      },
      yAxis: { type: "value", splitLine: { lineStyle: { color: c.grille } }, axisLabel: { color: c.texteSecondaire } },
      series: [
        {
          name: "Nominations",
          type: "bar",
          data: s.par_annee.map((a) => a.nominations),
          barWidth: 22,
          itemStyle: { color: c.serie1, borderRadius: [4, 4, 0, 0] },
        },
        {
          name: "Décisions",
          type: "bar",
          data: s.par_annee.map((a) => a.decisions),
          barWidth: 22,
          itemStyle: { color: c.serie2, borderRadius: [4, 4, 0, 0] },
        },
      ],
    }),
    monter(
      elTypes.value,
      barreH(
        c,
        s.decisions_par_type.map((d) => LIBELLES_TYPE[d.type] ?? d.type),
        s.decisions_par_type.map((d) => d.n),
      ),
    ),
    monter(
      elStructures.value,
      barreH(
        c,
        s.top_structures.map((d) => d.structure),
        s.top_structures.map((d) => d.mandats),
      ),
    ),
  );
});

onBeforeUnmount(() => nettoyages.forEach((fn) => fn()));
</script>
