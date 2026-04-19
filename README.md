# GMapProspect

Outil local de scraping Google Maps et de prospection commerciale.

Le projet tourne sur **la machine de l'utilisateur**.

- lancer le scraper Playwright sur son propre PC
- stocker ses prospects localement
- trier les fiches en mode dashboard ou swipe
- passer ses appels en mode focus
- retrouver l'historique des appels avec les notes et la durée

## Ce que fait le projet

- scrape des fiches Google Maps depuis une recherche
- exporte un `results.csv`
- alimente une base locale `prospects.db`
- maintient un fichier `prospects.json` pour l'agrégation des résultats
- propose plusieurs interfaces locales :
  - `/` : dashboard principal
  - `/swipe` : tri rapide des fiches
  - `/prospection` : mode appel focus
  - `/history` : historique des appels

## Stack

- Python
- Playwright + Chromium
- SQLite
- HTML / CSS / JS vanilla
- serveur HTTP local via `server.py`

## Installation

### 1. Cloner le dépôt

```bash
git clone <TON-REPO-GITHUB>
cd GMapProspect
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 4. Installer Chromium pour Playwright

```bash
python3 -m playwright install chromium
```

## Lancement rapide

### Option recommandée : lancer l'application locale

```bash
python3 server.py
```

Puis ouvrir :

```text
http://localhost:8000
```

Depuis cette interface, tu peux :

- lancer un scraping
- consulter les prospects
- changer leur statut
- prendre des notes
- utiliser le mode swipe
- utiliser le mode appel
- consulter l'historique d'appels

### Option CLI : lancer seulement le scraper

```bash
python3 main.py -s "hotels in Paris" -t 20
```

Arguments :

- `-s`, `--search` : requête Google Maps
- `-t`, `--total` : nombre de fiches à récupérer

## Données générées

Les données sont stockées localement dans le dossier du projet :

- `results.csv` : export CSV du dernier scraping
- `prospects.json` : agrégation JSON des prospects
- `prospects.db` : base SQLite locale

Le `.gitignore` ignore déjà :

- `prospects.db`
- `prospects.json`

## Workflow conseillé

1. Lancer `python3 server.py`
2. Ouvrir `http://localhost:8000`
3. Faire un scraping
4. Qualifier les fiches sur le dashboard ou via `/swipe`
5. Envoyer les fiches prometteuses dans le statut `Intéressé`
6. Utiliser `/prospection` pour passer les appels
7. Retrouver les appels terminés dans `/history`

## Historique des appels

Quand un appel est terminé depuis la page `/prospection`, l'application enregistre :

- la fiche appelée
- la note prise pendant l'appel
- la date de début
- la date de fin
- la durée de l'appel

Ces données sont visibles dans la page `/history`, avec :

- le nombre total d'appels
- le temps cumulé
- le temps moyen par appel
- la liste détaillée des appels passés

## Important

- Le scraping dépend d'un navigateur lancé localement via Playwright.
- Ce projet est donc pensé pour être exécuté **sur le PC de l'utilisateur**.
- Si tu partages ce repo sur GitHub, chaque personne pourra l'utiliser en local sans que tu héberges un service centralisé.
- Google Maps peut changer son HTML ou renforcer ses protections anti-bot, donc certains sélecteurs peuvent casser avec le temps.

## Commandes utiles

Installer / mettre à jour les dépendances :

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

Lancer l'application :

```bash
python3 server.py
```

Lancer un scraping direct :

```bash
python3 main.py -s "plombiers Lyon" -t 15
```

## Limites actuelles

- scraping dépendant de la structure actuelle de Google Maps
- certaines fiches peuvent être incomplètes
- les protections Google peuvent ralentir ou bloquer certains runs
- l'interface est locale, pas multi-utilisateur

## Licence

Voir [LICENSE](LICENSE).
