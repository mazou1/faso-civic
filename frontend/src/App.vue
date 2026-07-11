<template>
  <header class="entete">
    <div class="entete-inner">
      <router-link to="/" class="marque">Faso<span>Civic</span></router-link>
      <nav class="nav">
        <router-link to="/">Tableau de bord</router-link>
        <router-link to="/decisions">Décisions</router-link>
        <router-link to="/textes">Lois & décrets</router-link>
        <router-link to="/finances">Finances</router-link>
        <router-link to="/nominations">Nominations</router-link>
        <router-link to="/annuaire">Annuaire de l'État</router-link>
      </nav>
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
      <a href="/api/docs" target="_blank" rel="noopener">API ouverte</a>
    </div>
  </footer>
</template>
