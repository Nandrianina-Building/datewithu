# Date With U 🇲🇬❤️ — Phase 1 : Fondation

Squelette Django conforme au cahier des charges : authentification par
utilisateur personnalisé, dashboard utilisateur et dashboard admin de base,
configuration de site administrable, templates + CSS minimal.

## Ce que contient cette Phase 1

- Projet Django (`config/`) avec settings basés sur `.env` (django-environ)
- App `accounts` : modèle `User` personnalisé, inscription, connexion,
  déconnexion, édition de profil
- App `core` : page d'accueil, dashboard utilisateur, dashboard admin,
  modèle `SiteConfiguration` (singleton administrable : nom du site, devise,
  mode maintenance, fonctionnalités activables...)
- Django REST Framework installé et prêt (pour les endpoints AJAX des
  Phases 3+)
- ASGI prêt à recevoir Django Channels (Phase 7 — chat, notifications
  temps réel)

## Phase 2 — Contenu administrable

Ajoutée par-dessus la Phase 1, sans toucher au cœur (accounts/core) :

- `apps.locations` → `City` (villes, section 5)
- `apps.catalog` → `Category` (avec sous-catégories via `parent`, section 6),
  `Place` (lieux, section 6) + `PlaceImage` (galerie)
- `apps.moods` → `Mood` (ambiances, section 8)
- `apps.budgets` → `Budget` (tranches de budget modifiables, section 9)
- `apps.occasions` → `Occasion` (section 10)
- `apps.activities` → `Activity` (section 7), reliée à un lieu, une ville,
  des moods compatibles et des budgets compatibles
- `apps.api` → endpoints DRF **en lecture seule**, base du Date Builder
  AJAX de la Phase 3 :
  - `GET /api/cities/`
  - `GET /api/categories/` (avec sous-catégories imbriquées)
  - `GET /api/moods/`
  - `GET /api/budgets/`
  - `GET /api/occasions/`
  - `GET /api/places/?search=tana&city=1&category=2&budget=3&mood=1`
  - `GET /api/activities/?city=1&mood=2&budget=3&category=4`

Tout est enregistré dans le Django Admin (`/admin/`) avec `list_editable`
sur les champs `is_active`/`display_order` pour activer/désactiver du
contenu sans coder — conformément au principe de la section 4.

Pour peupler rapidement des données de test : utilise le Django Admin, ou
écris une commande `management command` / des fixtures dans une phase
suivante si tu veux automatiser le seed.

## Phase 3 — Date Builder dynamique

- `apps.planner` → `PreferenceQuestion` (section 11, administrable),
  `SpecialAttention` (« petites attentions »), `DatePlan` (le rendez-vous
  en cours de construction) + `DatePlanPreferenceAnswer`
- 7 étapes dynamiques, pilotées par Django (section 12) :
  `mood → city → place → activity → budget → schedule → final`
  (place/activity sont sautables — un lieu n'est pas obligatoire si
  l'utilisateur choisit juste une activité, et inversement)
- Endpoints AJAX (`apps.api.date_builder`) :
  - `POST /api/date-builder/start/` → crée un brouillon, renvoie l'étape 1
  - `GET  /api/date-builder/<id>/` → reprendre un brouillon (autosave)
  - `POST /api/date-builder/<id>/step/` → met à jour un champ, renvoie
    l'étape suivante + les options déjà filtrées (ville → lieux de cette
    ville, mood/budget → activités compatibles, etc. — section 14)
  - `POST /api/date-builder/<id>/complete/` → valide et finalise
    (statut `completed`), devient la base de l'invitation en Phase 4
- Page de démonstration : `/date-builder/` (connecté), avec
  `static/js/date-builder.js` — vanilla JS + `fetch`, aucun framework,
  pour rester lisible et facile à remplacer par React/Vue plus tard si
  tu veux.

**Hypothèse assumée** : les sections détaillées du cahier des charges
au-delà de la section ~20 n'étaient pas toutes lisibles dans le fichier
que tu m'as donné (troncature). J'ai donc défini moi-même l'ordre des 7
étapes et le modèle `SpecialAttention` de façon cohérente avec le reste
du document — dis-moi si le cahier des charges complet prévoit autre
chose et j'ajuste.

## Phase 4 — Invitations

- `apps.invitations` → modèle `Invitation` : token unique (UUID), statut
  (`pending → viewed → accepted/maybe/declined`, + `expired`/`cancelled`),
  compteur de vues, date d'expiration calculée depuis
  `SiteConfiguration.invitation_expiration_days`
- Endpoints AJAX (`apps.api.invitations`) :
  - `POST /api/invitations/create/` (créateur, connecté) → génère le lien
    à partir d'un `DatePlan` complété (ou renvoie l'invitation existante)
  - `GET /api/invitations/<token>/public/` (public) → détails vus par le
    partenaire, incrémente le compteur de vues
  - `POST /api/invitations/<token>/respond/` (public, pas de compte requis)
    → `{"response": "accept"|"maybe"|"decline"}`
  - `POST /api/invitations/<token>/cancel/` (créateur) → annule
  - `GET /api/my-dates/` (créateur) → liste "Mes rendez-vous" + statut
- Page publique `/invite/<token>/` **rendue côté serveur** avec balises
  Open Graph (section 98) pour un bel aperçu quand le lien est collé dans
  WhatsApp/Messenger — le compteur de vues n'est incrémenté que par le JS
  (donc pas faussé par les robots de prévisualisation qui ne lisent que le
  HTML)
- Le Date Builder (Phase 3) enchaîne maintenant automatiquement sur la
  création de l'invitation et affiche les boutons **Copier le lien /
  WhatsApp / Messenger** dès que le rendez-vous est finalisé
- Le dashboard utilisateur affiche désormais "Mes rendez-vous" avec le
  statut de chaque invitation (`static/js/my-dates.js`)

## Phase 5 — Dashboard utilisateur (favoris, notifications, historique)

- `apps.favorites` → `FavoritePlace`, `FavoriteActivity` (toggle en un clic)
- `apps.notifications` → `Notification`, créées automatiquement quand une
  invitation est vue ou qu'on y répond (branché directement dans
  `Invitation.mark_viewed()` / `.respond()`, Phase 4)
- Endpoints AJAX ajoutés à `apps.api` :
  - `POST /api/favorites/places/<id>/toggle/`,
    `POST /api/favorites/activities/<id>/toggle/`
  - `GET /api/favorites/` → favoris du créateur connecté
  - `GET /api/notifications/?unread=1`,
    `POST /api/notifications/<id>/read/`,
    `POST /api/notifications/read-all/`
  - `GET /api/my-dates/?when=upcoming|past` (historique filtrable) et
    `GET /api/my-dates/<id>/` (détail complet d'un rendez-vous)
- Dashboard utilisateur (`/dashboard/`) : les cartes "Mes rendez-vous",
  "Favoris" et "Notifications" sont maintenant branchées en AJAX
- Petit badge 🔔 dans la navbar (toutes les pages, si connecté) affichant
  le nombre de notifications non lues
- Nouvelle page `/explore/` : parcourir les lieux et les mettre en favori
  (cœur cliquable) — sert de démonstration bout-en-bout des favoris

## Phase 6 — Dashboard admin avancé

- Nouvelle permission `IsStaffUser` (`apps.api.permissions`) : toutes les
  vues admin de l'API la réutilisent plutôt que de dupliquer la
  vérification `is_staff` partout
- `GET /api/admin/stats/` → utilisateurs (total, nouveaux 7j/30j),
  rendez-vous (brouillons/complétés), invitations (répartition par
  statut + taux d'acceptation), lieux/activités actifs, villes et
  ambiances les plus demandées, derniers inscrits
- `GET /api/admin/dates/?status=&city=&when=upcoming|past` → vue
  d'ensemble de **tous** les rendez-vous, tous utilisateurs confondus
  (à ne pas confondre avec `/api/my-dates/`, scopé au créateur)
- `GET /api/admin/places/?active=0` + `POST /api/admin/places/<id>/toggle-active/`
  → file de modération des lieux (lieux inactifs en premier), activation
  en un clic sans repasser par `/admin/`
- `/dashboard/admin/` (Phase 1) est maintenant entièrement branché en
  AJAX avec ces trois blocs : statistiques, vue d'ensemble, modération

## Phase 7 — Communication (chat)

- `apps.chat` → `Conversation` (1 par rendez-vous) + `Message`
  (`from_creator` distingue les deux parties sans exiger que le/la
  partenaire ait un compte, comme pour les invitations en Phase 4)
- **Fonctionne dès maintenant, sans rien installer de plus** : chat en
  polling HTTP (`static/js/chat.js`, requête toutes les 3s)
  - `GET /api/chat/<date_plan_id>/messages/?token=...` → historique
    (marque aussi les messages de l'autre partie comme lus)
  - `POST /api/chat/<date_plan_id>/messages/` → envoyer un message
  - Accès : le créateur via sa session normale, le/la partenaire via le
    token de son invitation (même mécanisme que pour Accepter/Décliner)
  - Page côté créateur : `/dates/<plan_id>/chat/` (lien depuis "Mes
    rendez-vous" au dashboard)
  - Page côté partenaire : `/invite/<token>/chat/` (lien affiché après
    avoir répondu Accepte/Peut-être sur la page d'invitation)
  - Un message du/de la partenaire déclenche une notification interne
    pour le créateur (réutilise `apps.notifications`, Phase 5)

### Passer en vrai temps réel (WebSockets) — optionnel

Le polling HTTP suffit pour un MVP et ne demande aucune infra
supplémentaire. Pour du vrai temps réel avec Django Channels :

```bash
pip install -r requirements-realtime.txt
# renseigne REDIS_URL dans .env, puis démarre un Redis local
cp config/asgi_realtime_example.py config/asgi.py
```

Puis dans `config/settings.py`, ajoute `"channels"` et `"daphne"` à
`INSTALLED_APPS` (avant `django.contrib.staticfiles`) et :

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [env("REDIS_URL", default="redis://localhost:6379")]},
    },
}
```

Lance ensuite avec `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
au lieu de `runserver`. Le consumer (`apps/chat/consumers.py`) et son
routing (`apps/chat/routing.py`) sont déjà écrits et réutilisent le même
modèle `Message` — bascule transparente, aucune migration de données.

## Phase 8 — Fonctionnalités avancées

- **Carte interactive** (`/map/`) : Leaflet + tuiles OpenStreetMap —
  **aucune clé API requise**, contrairement à Google Maps. Affiche tous
  les lieux ayant une latitude/longitude renseignée (`/api/places/`
  expose maintenant ces champs)
- **Surprise Date** : bouton 🎲 sur le dashboard →
  `POST /api/date-builder/surprise/` tire au sort une ambiance, une
  ville (si non précisée), un lieu ou une activité compatible, un
  budget, et propose le prochain samedi 19h. Le DatePlan reste en
  brouillon : l'utilisateur peut ajuster avant de finaliser
- **Packages** (`apps.packages`, page `/packages/`) : rendez-vous
  pré-configurés par l'admin (lieu + activité + ambiance + budget déjà
  assemblés). `POST /api/packages/<id>/use/` crée un `DatePlan`
  pré-rempli, directement à l'étape "date & heure"
- **Avis** (`apps.reviews`, sur la page `/explore/`) : un avis par
  utilisateur et par lieu (`Review`, `unique_together`), la note
  moyenne du `Place` est recalculée automatiquement à chaque avis
  ajouté/modifié/supprimé
- **QR code** : affiché sur l'écran de partage du Date Builder, via
  l'API publique `api.qrserver.com` (image `<img>` générée côté
  navigateur du visiteur — zéro dépendance backend)
- **PWA** : `static/manifest.json`, `static/sw.js` (service worker
  "network-first", ne met jamais en cache les appels `/api/`), servi à
  la racine (`/sw.js`, nécessaire pour qu'il contrôle tout le site) —
  l'app est installable sur mobile. Une icône SVG minimale est fournie
  (`static/icons/icon.svg`) ; remplace-la par de vraies icônes
  PNG 192×192/512×512 avant mise en production (certains navigateurs
  n'acceptent pas encore le SVG seul dans le manifest)

Le Date Builder (`/date-builder/?plan=<id>`) sait maintenant reprendre
un `DatePlan` déjà créé (par un package ou une surprise date) au lieu
de toujours repartir de zéro.

## Résumé — les 8 phases sont livrées

Le MVP complet du cahier des charges est couvert : inscription →
contenu administrable → Date Builder dynamique → invitations
partageables → dashboard utilisateur (favoris/notifications/historique)
→ dashboard admin avancé → chat → fonctionnalités avancées.

Pistes pour la suite (hors phases initiales) : paiement en ligne,
application mobile native, tests automatisés, déploiement (Nginx +
Gunicorn/Daphne + PostgreSQL managé), CI/CD, vraies icônes PWA.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# édite .env : SECRET_KEY, DATABASE_URL (ou laisse vide pour SQLite en local)

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

Puis ouvre :

- `http://127.0.0.1:8000/` — accueil
- `http://127.0.0.1:8000/accounts/register/` — inscription
- `http://127.0.0.1:8000/dashboard/` — espace utilisateur (connecté)
- `http://127.0.0.1:8000/dashboard/admin/` — dashboard admin (staff)
- `http://127.0.0.1:8000/admin/` — Django Admin complet

## Base de données

Par défaut le projet utilise SQLite si `DATABASE_URL` n'est pas défini,
pour démarrer sans installer PostgreSQL. Pour du PostgreSQL local :

```bash
createdb datewithu
createuser datewithu --pwprompt
```

puis renseigne `DATABASE_URL=postgres://datewithu:motdepasse@localhost:5432/datewithu`
dans `.env`.

## Prochaine étape (Phase 2)

Créer les apps de contenu administrable (`locations` pour les villes,
`places` pour les lieux/catégories, `activities`, `moods`, `budgets`,
`occasions`) — chacune avec son modèle, son admin Django, et ses premiers
endpoints DRF en lecture seule pour préparer le Date Builder AJAX (Phase 3).
