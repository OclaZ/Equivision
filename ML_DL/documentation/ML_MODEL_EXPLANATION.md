# EquiVision ML Model: Premium Pricing Engine (Deep Dive)

This document provides a line-by-line technical autopsy of the Machine Learning pricing engine, including the "Stacking Ensemble" architecture and the "Synthetic Feature" generation logic.

## 1. Ensemble Architecture (Stacking)

We use a "Committee of Experts" (Level 0) whose results are judged by a "Master Learner" (Level 1).

```mermaid
graph TD
    A[Processed Horse Data] --> B[Level 0: RandomForest]
    A --> C[Level 0: HistGradientBoosting]
    A --> D[Level 0: XGBoost]
    A --> E[Level 0: GradientBoosting]
    
    B --> F[Prediction 1]
    C --> G[Prediction 2]
    D --> H[Prediction 3]
    E --> I[Prediction 4]
    
    F --> J[Level 1: Ridge Meta-Learner]
    G --> J
    H --> J
    I --> J
    
    J --> K[Final Estimated Price (EUR)]
    
    subgraph "The Expert Committee"
    B
    C
    D
    E
    end
    
    subgraph "The Final Judge"
    J
    end
```

---

## 2. Synthetic Feature Generation (Detailed Math)

We inject "Hidden Features" into the model to simulate unobserved real-world variables.

### A. Training Score (0-10)
**Code Analysis:**
```python
# 1: age_component = 5.0 * np.exp(-0.5 * ((age - 7.5) / 4.5) ** 2)
#    This creates a PEAK value at age 7.5. It uses a Gaussian (bell) curve.
# 2: breed_component = tier * 0.8
#    Adds 'quality points' based on the sport tier of the breed.
# 3: score = age_component + breed_component + rng.normal(0, 1.8)
#    CRITICAL: rng.normal(0, 1.8) adds 'Noise'. This noise represents 
#    unobserved factors like "Did the rider have a good coach?".
```

### B. Health Score (0-10)
**Code Analysis:**
```python
# 1: age_component = 8.0 - (age / 30.0) * 4.0
#    Linear decline of health as the horse gets older.
# 2: price_component = np.clip((price_log - 8.0) / 2.0, -1, 1.5) * 1.0
#    Positive correlation: expensive horses are assumed to have 
#    better medical maintenance/veterinary care.
```

---

## 3. The Pricing Pipeline Flow (`pipeline.py`)

```python
# 1: df["age_value_curve"] = df["age"].apply(lambda a: exp(...))
#    Encodes the 'Prime Age' theory (horses are worth most at 6-8 years).
# 2: y = np.log1p(df["price"])
#    CRITICAL: Most horses cost 2k–10k, but some cost 100k+. 
#    The 'Log' transform squashes these extremes so the model 
#    isn't distracted by 'Outlier' prices.
# 3: preprocessor = ColumnTransformer(...)
#    Standardizes the data:
#    - Categorical (Breed): Becomes 'One-Hot' vectors.
#    - Numerical (Height): Becomes 'Standard Scaled' (mean=0, std=1).
# 4: searcher = RandomizedSearchCV(pipeline, param_grid, cv=5)
#    The model 'competes' against itself 30 times with different settings 
#    to find the perfect 'Hyperparameters'.
```

---

## 4. Why Stacking?

Instead of just choosing one model, we use **StackingRegressor**. 
- **RandomForest** is good at seeing "Is it a Pony AND is it White?".
- **XGBoost** is good at seeing subtle price trends across the whole market.
- **The Ridge Meta-Learner** learns that when RandomForest says "5,000" and XGBoost says "7,000", the truth is usually "6,200".

**Final result**: A price prediction that is resilient to errors in any single algorithm.
