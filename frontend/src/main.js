import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./styles.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "accueil", component: () => import("./views/AccueilView.vue") },
    { path: "/decisions", name: "decisions", component: () => import("./views/DecisionsView.vue") },
    { path: "/textes", name: "textes", component: () => import("./views/TextesView.vue") },
    { path: "/finances", name: "finances", component: () => import("./views/FinancesView.vue") },
    { path: "/nominations", name: "nominations", component: () => import("./views/NominationsView.vue") },
    { path: "/annuaire", name: "annuaire", component: () => import("./views/AnnuaireView.vue") },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

createApp(App).use(router).mount("#app");
