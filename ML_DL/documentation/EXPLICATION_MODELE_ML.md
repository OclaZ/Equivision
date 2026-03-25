# EquiVision Machine Learning : Moteur de Prix Premium (Détails Techniques)

Ce document explique le fonctionnement interne du pipeline de tarification (v3) d'EquiVision, décrivant comment nous passons de données brutes à une estimation de prix précise.

---

## 1. Architecture de l'Ensemble (Stacking)

Au lieu d'utiliser un seul algorithme, nous utilisons un **Comité d'Experts** dont les résultats sont arbitrés par un **Maitre d'Apprentissage**.

```mermaid
graph TD
    A[Données du Cheval Traitées] --> B[Expert 1: RandomForest]
    A --> C[Expert 2: HistGradientBoosting]
    A --> D[Expert 3: XGBoost]
    A --> E[Expert 4: GradientBoosting]
    
    B --> F[Prédiction 1]
    C --> G[Prédiction 2]
    D --> H[Prédiction 3]
    E --> I[Prédiction 4]
    
    F --> J[Arbitre : Ridge Meta-Learner]
    G --> J
    H --> J
    I --> J
    
    J --> K[Prix Estimé Final (EUR)]
    
    subgraph "Le Comité d'Experts"
    B;C;D;E
    end
    
    subgraph "Le Juge Final"
    J
    end
```

---

## 2. Les "Caractéristiques Synthétiques" (Innovation Majeure)

Les jeux de données standards manquent souvent d'informations cruciales (ex: *Est-ce que le cheval est facile à monter ?*). Nous simulons ces variables "cachées" avec des générateurs mathématiques injectant du bruit réaliste.

### A. Score d'Entraînement / Éducation (0-10)
**Analyse Mathématique :**
```python
# component = 5.0 * np.exp(-0.5 * ((age - 7.5) / 4.5) ** 2)
# Pourquoi ? Nous utilisons une courbe en cloche (Gaussienne) pour 
# que le score d'entraînement soit maximal à 7.5 ans (le pic de carrière).
# score = base + rng.normal(0, 1.8)
# Pourquoi le bruit ? Le 'bruit' simule les facteurs que l'IA ne voit pas, 
# comme la qualité du coach ou de l'écurie.
```

### B. Score de Santé (0-10)
**Analyse Mathématique :**
```python
# age_component = 8.0 - (age / 30.0) * 4.0
# La santé décline de manière linéaire avec l'âge (perte de 4 points sur 30 ans).
# price_component = np.clip((price_log - 8.0) / 2.0, -1, 1.5) * 1.0
# Nous supposons que les chevaux plus chers ont bénéficié de meilleurs soins vétérinaires.
```

---

## 3. Le Pipeline de Prix (`pipeline.py`)

```python
# 1: y = np.log1p(df["price"])
#    IMPORTANCE : Les prix immobiliers et équins sont très "étalés". 
#    Le logarithme écrase les prix extrêmes (ex: un cheval à 200k€) 
#    pour que l'IA puisse se concentrer sur le marché moyen sans être perdue.
# 2: preprocessor = ColumnTransformer(...)
#    Cette étape standardise tout :
#    - Les races deviennent des vecteurs (One-Hot).
#    - Les tailles sont centrées sur 0 (StandardScaler).
# 3: RandomizedSearchCV(pipeline, param_grid, cv=5)
#    L'intelligence artificielle "s'entraîne contre elle-même" 30 fois 
#    pour trouver les paramètres parfaits (Hyperparamètres).
```

---

## 4. Pourquoi le "Stacking" est-il nécessaire ?

Chaque modèle a ses faiblesses :
-   **RandomForest** voit bien les règles simples (ex: "S'il fait moins d'1m48, c'est un poney").
-   **XGBoost** voit bien les tendances complexes de tout le marché.
-   Le **Ridge Meta-Learner** apprend à quel expert faire confiance selon le type de cheval.

**Résultat final** : Une prédiction de prix robuste qui résiste aux erreurs individuelles d'un seul algorithme, garantissant une estimation fiable sur le marché d'Avito et Maroc-Annuaire.
