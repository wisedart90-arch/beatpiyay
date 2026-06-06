# 🎵 BeatPiyay — Guide de démarrage local

> Plateforme marketplace de beats musicaux. Surpasse Beatstars.

---

## Prérequis

- Python 3.11+
- Node.js 20+
- MongoDB 7+ (local ou [MongoDB Atlas](https://cloud.mongodb.com) gratuit)
- Git

---

## 🚀 Installation en 5 minutes

### 1. Clone & variables d'environnement

```bash
git clone https://github.com/ton-user/beatpiyay.git
cd beatpiyay

# Backend
cp .env.example .env
# → Ouvre .env et remplis JWT_SECRET_KEY, MONGO_URL, etc.
# Génère un secret solide :
openssl rand -hex 32
```

### 2. Backend (FastAPI)

```bash
cd backend

# Crée un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Lance le serveur dev
uvicorn main:app --reload --port 8000
```

API disponible sur : http://localhost:8000
Docs interactives : http://localhost:8000/api/docs

### 3. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

App disponible sur : http://localhost:5173

---

## 📁 Structure du projet

```
beatpiyay/
├── .env.example          ← Template variables (copier → .env)
├── .gitignore            ← Protège .env et node_modules
├── backend/
│   ├── main.py           ← App FastAPI principale
│   ├── requirements.txt  ← Dépendances Python
│   ├── middleware/
│   │   └── auth.py       ← JWT verify + dépendances FastAPI
│   └── routes/
│       ├── auth.py       ← Register / Login
│       ├── beats.py      ← CRUD beats (avec filtres, pagination)
│       ├── licenses.py   ← Basic / Premium / Exclusive
│       ├── producers.py  ← Profils producteurs
│       └── payments.py   ← Stub Stripe (à brancher)
└── frontend/
    ├── package.json      ← Dépendances nettoyées (sans Emergent)
    └── src/
        ├── pages/        ← Home, Beats, BeatDetail, Login...
        ├── components/   ← Navbar, Player, LicenseModal...
        ├── hooks/        ← useAuth, useBeats, usePlayer...
        ├── context/      ← AuthContext, CartContext
        └── api/          ← Appels axios vers le backend
```

---

## 🔒 Sécurité — ce qui a été corrigé vs le projet original

| Problème original | Correction BeatPiyay |
|---|---|
| `.env` commité avec secrets | `.env` dans `.gitignore`, `.env.example` à la place |
| `CORS_ORIGINS=*` avec credentials | CORS explicite par origine, liste configurable |
| Pas d'auth sur les routes | JWT Bearer obligatoire sur toutes les routes sensibles |
| Middleware après les routes | CORS ajouté **avant** `include_router()` |
| `@app.on_event` déprécié | `lifespan` context manager moderne |
| Pas de validation des inputs | Pydantic avec min/max sur chaque champ |
| Pas de gestion d'erreurs DB | try/except + index MongoDB créés au démarrage |
| Dépendance privée Emergent | Supprimée — inutile en dehors de leur plateforme |
| `react-scripts` (CRA) | Remplacé par **Vite** (10x plus rapide) |
| Deux libs de dates | Une seule : `date-fns` |
| Deux libs de fetching | Une seule : `@tanstack/react-query` |

---

## 🎯 Roadmap

- [ ] Upload audio (S3 / stockage local)
- [ ] Intégration Stripe Checkout
- [ ] Player audio HTML5 persistant
- [ ] Dashboard analytics producteur
- [ ] Système de notifications
- [ ] Recherche full-text MongoDB Atlas Search

---

## Commission

BeatPiyay prend **5%** par transaction.
Beatstars prend **30%** + abonnement mensuel obligatoire.
