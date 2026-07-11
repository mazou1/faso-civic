<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const q = ref("");

function chercher() {
  if (q.value.trim().length >= 2) {
    router.push({ path: "/recherche", query: { q: q.value.trim() } });
    q.value = "";
  }
}
</script>

<template>
  <header class="entete">
    <div class="entete-inner">
      <router-link to="/" class="marque">Faso<span>Civic</span></router-link>
      <nav class="nav">
        <router-link to="/">Tableau de bord</router-link>
        <router-link to="/actualites">Actualités</router-link>
        <router-link to="/gouvernement">Gouvernement</router-link>
        <router-link to="/assemblee">Assemblée</router-link>
        <router-link to="/conseils">Conseil des ministres</router-link>
        <router-link to="/textes">Lois & décrets</router-link>
        <router-link to="/finances">Finances</router-link>
        <router-link to="/annuaire">Annuaire de l'État</router-link>
        <a href="/plan-relance/">Plan de relance</a>
      </nav>
      <input
        v-model="q"
        class="recherche-globale"
        type="search"
        placeholder="Rechercher…"
        aria-label="Recherche globale"
        @keyup.enter="chercher"
      />
    </div>
  </header>
  <main>
    <div class="conteneur">
      <router-view />
    </div>
  </main>
  <footer class="pied">
    <div class="conteneur">
      <span>Plateforme citoyenne indépendante — données issues des sources officielles, chaque entrée liée à son document d'origine.</span>
      <router-link to="/a-propos">À propos & méthodologie</router-link>
      <a href="/api/docs" target="_blank" rel="noopener">API ouverte</a>
    </div>
  </footer>
</template>
