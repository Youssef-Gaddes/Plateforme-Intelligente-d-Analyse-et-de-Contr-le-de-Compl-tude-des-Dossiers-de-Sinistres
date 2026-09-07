# Plateforme Intelligente d'Analyse et de Contrôle de Complétude des Dossiers de Sinistres

Plateforme web permettant l'automatisation du contrôle de complétude des dossiers de sinistres d'assurance, à l'aide de reconnaissance optique de caractères (OCR) et de classification automatique de documents.

Projet réalisé dans le cadre d'un stage chez **Vermeg** (06/07/2026 – 06/09/2026).

## Sommaire

- [Contexte](#contexte)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Modèle de données](#modèle-de-données)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Tests](#tests)
- [Rôles et permissions](#rôles-et-permissions)
- [Limites connues](#limites-connues)
- [Perspectives d'amélioration](#perspectives-damélioration)
- [Documentation complète](#documentation-complète)

## Contexte

La gestion manuelle des dossiers de sinistres présente plusieurs limites : lenteur de traitement, risque d'erreur humaine dans la vérification de la complétude, et absence de visibilité globale sur l'avancement des dossiers. Ce projet vise à démontrer comment l'IA (OCR + classification documentaire) peut réduire le temps de traitement tout en fiabilisant la détection des pièces manquantes.

## Fonctionnalités

- **Upload de documents** (PDF, PNG, JPG) avec validation de format et de taille (10 Mo max)
- **OCR automatique** avec prétraitement d'image (débruitage, correction d'éclairage, seuillage adaptatif, redressement)
- **Classification automatique** des documents parmi 7 catégories (déclaration de sinistre, carte grise, permis de conduire, facture, devis, constat amiable, rapport d'expertise)
- **Calcul d'un score de complétude** par dossier, selon les pièces obligatoires requises par type de sinistre
- **Révision manuelle** des documents dont la confiance de classification est trop faible
- **Tableau de bord** avec indicateurs globaux, répartition par type de dossier/document, et alertes sur les documents à réviser
- **Gestion des droits** par rôle (administrateur, gestionnaire, lecteur), avec un modèle de propriété des dossiers

## Architecture

```
┌─────────────────┐      REST / HTTPS      ┌──────────────────┐
│  Frontend        │ ─────────────────────▶ │  Backend          │
│  Angular         │ ◀───────────────────── │  FastAPI          │
└─────────────────┘                         └────────┬─────────┘
                                                       │
                                     ┌─────────────────┼─────────────────┐
                                     ▼                 ▼                 ▼
                              ┌───────────┐   ┌────────────────┐  ┌───────────┐
                              │   OCR      │   │ Classification │  │ Score de  │
                              │ (Tesseract)│   │ (TF-IDF + LR)  │  │complétude │
                              └───────────┘   └────────────────┘  └───────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │   PostgreSQL      │
                                              └──────────────────┘
```

## Stack technique

| Couche | Technologie |
|---|---|
| Frontend | Angular |
| Backend | FastAPI (Python) |
| Base de données | PostgreSQL |
| ORM / Migrations | SQLAlchemy + Alembic |
| OCR | Tesseract (via pytesseract) + OpenCV (prétraitement) |
| Classification | scikit-learn (TF-IDF + régression logistique) |
| Authentification | JWT (HTTPBearer) + bcrypt |
| Tests | pytest + client de test FastAPI |

## Modèle de données

Trois tables principales :

- **users** : id, name, email, password (haché), role (`admin` / `gestionnaire` / `lecteur`)
- **claims** : id, claim_number, insured_name, status, claim_type (`auto` / `habitation` / `santé`), user_id (FK vers le lecteur propriétaire), completeness_score, creation_date
- **documents** : id, claim_id (FK), file_name, file_path, document_type, ocr_text, classification_confidence, is_manually_reviewed, upload_date

Les migrations sont gérées avec Alembic ; le schéma peut être reconstruit intégralement à partir de l'historique des migrations versionnées.

## Installation

### Prérequis

- Python 3.x
- Node.js + npm / Angular CLI
- PostgreSQL
- Tesseract OCR (avec le modèle linguistique français)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt

# Configurer les variables d'environnement (.env) : DATABASE_URL, SECRET_KEY, etc.

alembic upgrade head
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
ng serve
```

L'application est ensuite accessible sur `http://localhost:4200`, avec l'API sur `http://localhost:8000` (documentation interactive sur `/docs`).

## Utilisation

1. Créer un compte administrateur via `/auth/register`
2. Créer des utilisateurs lecteurs (assurés) et gestionnaires
3. Un gestionnaire crée un dossier de sinistre et l'associe à un lecteur
4. Le lecteur (ou le gestionnaire) téléverse les documents justificatifs
5. Chaque document est automatiquement passé par l'OCR puis classifié
6. Le score de complétude du dossier se met à jour en conséquence
7. Les documents à faible confiance de classification apparaissent dans la file de révision manuelle

## Tests

Une suite de 39 tests fonctionnels couvre l'authentification, la gestion des dossiers (avec le modèle de propriété) et la gestion des documents.

```bash
cd backend
pytest
```

Les endpoints d'OCR et de classification sont testés via des implémentations simulées (mocks) pour garantir la reproductibilité des tests.

## Rôles et permissions

| Action | Admin | Gestionnaire | Lecteur |
|---|:---:|:---:|:---:|
| Gestion des utilisateurs | ✅ | ❌ | ❌ |
| Création / modification d'un dossier | ✅ | ✅ | ❌ |
| Suppression d'un dossier | ✅ | ❌ | ❌ |
| Consultation des dossiers | Tous | Tous | Ses dossiers uniquement |
| Upload de documents | Tous dossiers | Tous dossiers | Ses dossiers uniquement |
| Révision manuelle d'un document | ✅ | ✅ | ❌ |

## Limites connues

- L'écriture manuscrite cursive reste mal reconnue par Tesseract
- Les plaques d'immatriculation tunisiennes (chiffres latins + arabe) sont mal extraites, faute du modèle linguistique arabe
- Le jeu de données de classification reste inégalement couvert pour certaines catégories (carte grise, rapport d'expertise)
- L'interface n'est pas encore entièrement traduite en français

## Perspectives d'amélioration

- Support du modèle linguistique arabe pour l'OCR
- Enrichissement du jeu de données réel pour la classification
- Conteneurisation complète (Docker Compose)
- Harmonisation linguistique complète du frontend

## Documentation complète

Pour le détail des choix de conception, des difficultés rencontrées et de la méthodologie de test, voir le rapport de stage complet : `Rapport_de_stage_Youssef_Gaddes.pdf`

---

**Auteur** : Youssef Gaddes
**Encadrant** : Hedi Hachani
**Année universitaire** : 2025/2026
