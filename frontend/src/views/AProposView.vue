<template>
  <h1>À propos</h1>
  <p class="sous-titre">Ce que ce site est, d'où viennent les données, et comment elles sont traitées.</p>

  <div class="liste" style="max-width: 780px">
    <section class="item">
      <h2>La mission</h2>
      <div class="detail">
        <p>
          FasoCivic est une <strong>plateforme citoyenne indépendante</strong> qui rend l'information
          publique du Burkina Faso accessible et interrogeable : décisions du Conseil des ministres,
          nominations officielles, textes de loi, engagements financiers de l'État.
        </p>
        <p>
          Ce projet n'est affilié à aucun gouvernement, parti ou organisation politique. Il ne publie
          <strong>que des informations déjà publiques</strong>, issues des sites officiels, et chaque
          donnée affichée est reliée à son document source — vous pouvez toujours vérifier par vous-même.
        </p>
      </div>
    </section>

    <section class="item">
      <h2>Les sources</h2>
      <div class="detail">
        <ul>
          <li>
            <a href="https://gouvernement.gov.bf" target="_blank" rel="noopener">gouvernement.gov.bf</a>
            — comptes rendus officiels du Conseil des ministres (texte intégral ou PDF).
          </li>
          <li>
            <a href="https://www.legiburkina.gov.bf" target="_blank" rel="noopener">Légiburkina (SGG-CM)</a>
            — décrets, lois, arrêtés et autres textes juridiques, avec leur Journal officiel de publication
            (<a href="https://www.jobf.gov.bf" target="_blank" rel="noopener">jobf.gov.bf</a>).
          </li>
          <li>
            <a href="https://www.presidencedufaso.bf" target="_blank" rel="noopener">presidencedufaso.bf</a>
            — communiqués de la Présidence du Faso.
          </li>
        </ul>
        <p>
          La collecte est automatique : toutes les 30 minutes pour les communiqués, chaque jeudi soir
          pour le Conseil des ministres, chaque matin pour les textes juridiques. Les documents
          originaux (HTML, PDF) sont archivés tels quels au moment de la collecte.
        </p>
      </div>
    </section>

    <section class="item">
      <h2>La méthode</h2>
      <div class="detail">
        <ol>
          <li><strong>Collecte</strong> — les documents sont récupérés depuis les sites officiels et archivés à l'identique.</li>
          <li><strong>Extraction</strong> — un modèle d'intelligence artificielle structure la prose officielle
            (décisions, nominations, montants), avec un score de confiance pour chaque information extraite.</li>
          <li><strong>Validation humaine</strong> — rien n'est publié automatiquement : chaque décision, nomination
            ou engagement est revu avant d'apparaître sur ce site.</li>
          <li><strong>Traçabilité</strong> — chaque information affichée porte le lien vers le compte rendu ou
            le texte officiel dont elle provient.</li>
        </ol>
      </div>
    </section>

    <section class="item">
      <h2>Les limites</h2>
      <div class="detail">
        <p>
          L'extraction automatique peut contenir des erreurs malgré la validation — un montant mal converti,
          une fonction mal rattachée. Les intitulés des ministères sont ceux en vigueur à la date de chaque
          document : un même ministère peut apparaître sous plusieurs noms au fil des remaniements.
          Les statistiques financières reflètent <em>ce qui est annoncé en Conseil des ministres</em>,
          pas l'exécution réelle des dépenses. En cas de doute, la source officielle fait toujours foi.
        </p>
      </div>
    </section>

    <section class="item">
      <h2>Ouvert, réutilisable</h2>
      <div class="detail">
        <p>
          Les données sont accessibles librement via une
          <a href="/api/docs" target="_blank" rel="noopener">API publique documentée</a>, et le code de la
          plateforme est open source (licence GPL-3.0). Ce projet s'inspire de
          <a href="https://www.vie-publique.sn" target="_blank" rel="noopener">vie-publique.sn</a>
          (Code for Senegal).
        </p>
      </div>
    </section>
  </div>
</template>
