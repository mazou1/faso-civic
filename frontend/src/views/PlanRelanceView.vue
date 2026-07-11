<template>
  <p style="margin: 0 0 10px"><router-link to="/dossiers">← Tous les dossiers</router-link></p>
  <iframe
    class="cadre-dossier"
    src="/plan-relance/"
    title="Plan de relance — PND R.E.L.A.N.C.E. 2026-2030"
    loading="eager"
  ></iframe>
</template>

<style scoped>
.cadre-dossier {
  width: 100%;
  height: calc(100dvh - 215px);
  min-height: 540px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #0b0e14; /* fond du dossier — évite un flash blanc au chargement */
}
@media (max-width: 768px) {
  /* barre de navigation basse : on lui laisse la place */
  .cadre-dossier { height: calc(100dvh - 250px); }
}
</style>
