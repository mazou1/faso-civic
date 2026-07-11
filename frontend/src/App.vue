<script setup>
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();
const q = ref("");
const menuOuvert = ref(false);
const theme = ref(document.documentElement.dataset.theme || "");

function chercher() {
  if (q.value.trim().length >= 2) {
    router.push({ path: "/recherche", query: { q: q.value.trim() } });
    q.value = "";
  }
}

function basculerTheme() {
  const sombreSysteme = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const effectif = theme.value || (sombreSysteme ? "dark" : "light");
  theme.value = effectif === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme.value;
  localStorage.setItem("theme", theme.value);
}

// fermer la feuille de menu à chaque navigation
watch(() => route.fullPath, () => (menuOuvert.value = false));

const LIENS = [
  ["/", "Tableau de bord"],
  ["/actualites", "Actualités"],
  ["/gouvernement", "Gouvernement"],
  ["/assemblee", "Assemblée"],
  ["/conseils", "Conseil des ministres"],
  ["/textes", "Lois & décrets"],
  ["/finances", "Finances"],
  ["/annuaire", "Annuaire de l'État"],
  ["/documents", "Documents"],
  ["/dossiers", "Dossiers"],
];
</script>

<template>
  <header class="entete">
    <div class="entete-inner">
      <router-link to="/" class="marque">Faso<span>Civic</span></router-link>
      <nav class="nav">
        <router-link v-for="[chemin, libelle] in LIENS" :key="chemin" :to="chemin">{{ libelle }}</router-link>
      </nav>
      <input
        v-model="q"
        class="recherche-globale"
        type="search"
        placeholder="Rechercher…"
        aria-label="Recherche globale"
        @keyup.enter="chercher"
      />
      <button
        class="btn-theme"
        :title="theme === 'dark' ? 'Passer en clair' : 'Passer en sombre'"
        aria-label="Basculer le thème clair/sombre"
        @click="basculerTheme"
      >
        {{ theme === "dark" ? "☀️" : "🌙" }}
      </button>
    </div>
  </header>

  <main>
    <div class="conteneur">
      <router-view v-slot="{ Component }">
        <!-- la clé inclut le thème : les graphiques relisent leurs couleurs au
             remontage ; le wrapper mono-racine porte l'animation d'entrée
             (les vues sont multi-racines, incompatibles avec <transition>) -->
        <div :key="route.fullPath + theme" class="vue-page">
          <component :is="Component" />
        </div>
      </router-view>
    </div>
  </main>

  <footer class="pied">
    <div class="conteneur">
      <span>Plateforme citoyenne indépendante — données issues des sources officielles, chaque entrée liée à son document d'origine.</span>
      <router-link to="/glossaire">Glossaire</router-link>
      <router-link to="/a-propos">À propos & méthodologie</router-link>
      <a href="/api/docs" target="_blank" rel="noopener">API ouverte</a>
    </div>
  </footer>

  <nav class="nav-mobile">
    <router-link to="/"><span class="icone">🏠</span><span>Accueil</span></router-link>
    <router-link to="/actualites"><span class="icone">📰</span><span>Actus</span></router-link>
    <router-link to="/conseils"><span class="icone">🏛️</span><span>Conseil</span></router-link>
    <router-link to="/finances"><span class="icone">💰</span><span>Finances</span></router-link>
    <button aria-label="Ouvrir le menu" @click="menuOuvert = !menuOuvert">
      <span class="icone">☰</span><span>Menu</span>
    </button>
  </nav>

  <div v-if="menuOuvert" class="voile-menu" @click="menuOuvert = false">
    <nav class="feuille-menu" @click.stop>
      <router-link v-for="[chemin, libelle] in LIENS" :key="chemin" :to="chemin">{{ libelle }}</router-link>
      <a href="/plan-relance/">Plan de relance</a>
      <router-link to="/glossaire">Glossaire</router-link>
    </nav>
  </div>
</template>
