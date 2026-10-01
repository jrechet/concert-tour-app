# AGENTS.md — concert-tour-app

Application FastAPI + HTMX de gestion de tournées (dates, salles, logistique), cible de
démonstration des cycles de TheSwarm (voir [README.md](README.md) et `theswarm.yaml`).

## Build & tests

```bash
pip install -r requirements.txt
pytest -v
```

## CI/CD disponibles

Le dépôt est hybride : il vit sur GitHub (référence) et sur la forge Forgejo
`https://forge.jrec.fr/jrechet/concert-tour-app` (suiveur).

- **GitHub Actions** (`.github/workflows/`) : pas de CI de PR ; seul
  `mirror-to-forge.yml` y tourne (sur `ubuntu-latest`, dépôt public). Rien ne déploie.
  Suivi d'un run : `gh run list --branch <branche>`, `gh run view <id> --log-failed`.
- **Forge** : `mirror-to-forge.yml` recopie chaque branche et tag sur la forge (secret
  `FORGE_TOKEN`, posé par le propriétaire). La forge n'exécute que
  `.forgejo/workflows/ci.yml`, un workflow minimal (checkout + `echo`) sur
  `[self-hosted, jre-server]`, qui garantit surtout que Forgejo n'exécute jamais
  `.github/workflows/`. Une vraie CI (`pytest`) s'ajouterait des deux côtés, mêmes
  commandes, jamais de déploiement côté forge, jamais d'action propre à GitHub.
  Suivi : `ssh jrec.fr '~/dev/server-app/forgejo/forge-tool.sh runs concert-tour-app'`.
- **Un seul endroit déploie** : GitHub, tant qu'il reste la référence.
