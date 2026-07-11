<template>
  <!-- plein écran sous l'en-tête : un seul défilement, celui du dossier -->
  <iframe
    class="cadre-dossier"
    :style="{ top: hautPx, height: hauteur }"
    src="/plan-relance/"
    title="Plan de relance — PND R.E.L.A.N.C.E. 2026-2030"
  ></iframe>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";

const hautPx = ref("0px");
const hauteur = ref("100dvh");

function mesurer() {
  const entete = document.querySelector(".entete");
  const haut = entete ? Math.round(entete.getBoundingClientRect().height) : 0;
  // un iframe est un élément remplacé : top+bottom ne l'étirent pas, la hauteur
  // doit être explicite ; sur mobile on réserve la barre de navigation basse
  const bas = window.innerWidth <= 768 ? "54px + env(safe-area-inset-bottom)" : "0px";
  hautPx.value = `${haut}px`;
  hauteur.value = `calc(100dvh - ${haut}px - (${bas}))`;
}

onMounted(() => {
  mesurer();
  window.addEventListener("resize", mesurer);
});
onBeforeUnmount(() => window.removeEventListener("resize", mesurer));
</script>

<style scoped>
.cadre-dossier {
  position: fixed;
  left: 0;
  width: 100%;
  border: 0;
  background: #0b0e14; /* fond du dossier — pas de flash blanc */
  z-index: 10; /* sous l'en-tête (60) et la nav mobile (70) */
}
</style>
