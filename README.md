# Agenda de Loïs

Site qui affiche l'emploi du temps HyperPlanning de Centrale Lille, mis à jour toutes les heures par GitHub Actions et hébergé gratuitement sur GitHub Pages.

## Contenu

- `index.html` : la page (vue semaine sur ordinateur, vue jour sur téléphone).
- `scripts/fetch_ics.py` : télécharge le .ics et le convertit en `data/events.json`.
- `.github/workflows/update.yml` : lance le script toutes les heures et publie le site.
- `data/events.json` : les cours (rempli automatiquement).

## Mise en ligne

1. Crée un dépôt **public** nommé `agenda` sur GitHub.
2. Envoie tous les fichiers du dossier, y compris le dossier caché `.github`.
3. Dans **Settings → Secrets and variables → Actions**, crée un secret `ICS_URL` contenant ton lien iCal.
4. Dans **Settings → Pages**, choisis **Source : GitHub Actions**.
5. Dans l'onglet **Actions**, ouvre « Mettre à jour l'agenda » puis clique sur **Run workflow**.
6. Le site est en ligne sur `https://<ton-pseudo>.github.io/agenda/`.

## Bon à savoir

- Ton lien iCal reste secret, mais les cours affichés sur le site sont publics.
- Si le dépôt n'a aucune activité pendant 60 jours (vacances d'été), GitHub met en pause la mise à jour automatique. Il suffit de la réactiver dans l'onglet Actions.
