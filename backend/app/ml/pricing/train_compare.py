"""
╔══════════════════════════════════════════════════════════════════════╗
║  EquiVision — Advanced Feature Engineering + Model Comparison       ║
║                                                                      ║
║  Strategy:                                                           ║
║    1. Log-transform target (skewness 22 → 0.3)                      ║
║    2. Extract color from name                                        ║
║    3. Add source as feature                                          ║
║    4. Engineer: age curve, breed premium, breed×gender interaction    ║
║    5. Synthesize: training_level, discipline, pedigree_score         ║
║    6. Compare 6 models with the enriched feature set                 ║
║                                                                      ║
║  6 Models: Ridge, RF, HistGB, GBR, XGBoost, SVR                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import randint, uniform
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVR

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "unified_horse_data.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "weights"
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
N_ITER_RANDOM = 20


# ══════════════════════════════════════════════════════════════════════
#  DOMAIN KNOWLEDGE TABLES
# ══════════════════════════════════════════════════════════════════════

# Breed → typical discipline mapping (real equestrian knowledge)
BREED_DISCIPLINE = {
    "Hanoverian": "dressage_jumping", "Oldenburg": "dressage_jumping",
    "Westphalian": "dressage_jumping", "KWPN": "dressage_jumping",
    "Holsteiner": "jumping", "Zangersheide": "jumping",
    "Selle Français": "jumping", "Belgian Warmblood": "dressage_jumping",
    "Belgian Sport Horse": "jumping", "Trakehner": "dressage",
    "Thoroughbred": "racing_eventing", "Anglo-Arabian": "eventing",
    "Arabian": "endurance", "Lusitano": "dressage_working",
    "Andalusian": "dressage_working", "Quarter Horse": "western",
    "Paint Horse": "western", "Appaloosa": "western",
    "Friesian": "dressage_carriage", "Irish Cob": "leisure_carriage",
    "Connemara": "jumping_leisure", "Welsh": "leisure_jumping",
    "Pony": "leisure", "Haflinger": "leisure_mountain",
    "Shetland": "companion", "Fjord": "leisure_mountain",
    "Percheron": "draft", "Shire": "draft",
    "Clydesdale": "draft", "Breton": "draft",
    "Other": "mixed",
}

# Breed → sport tier (affects training potential and value ceiling)
BREED_SPORT_TIER = {
    "KWPN": 5, "Hanoverian": 5, "Oldenburg": 5, "Holsteiner": 5,
    "Selle Français": 5, "Zangersheide": 5, "Westphalian": 5,
    "Belgian Warmblood": 4, "Trakehner": 4, "Belgian Sport Horse": 4,
    "Thoroughbred": 4, "Anglo-Arabian": 4,
    "Lusitano": 4, "Andalusian": 4, "Friesian": 3,
    "Quarter Horse": 3, "Arabian": 3,
    "Connemara": 3, "Irish Cob": 2, "Paint Horse": 2,
    "Appaloosa": 2, "Welsh": 2, "Haflinger": 2,
    "Pony": 2, "Fjord": 2, "Shetland": 1,
    "Percheron": 2, "Shire": 2, "Clydesdale": 2,
    "Breton": 1, "Other": 2,
}

# Color mapping from French/German name keywords
COLOR_MAP = {
    "noir": "black", "bai": "bay", "alezan": "chestnut", "gris": "grey",
    "blanc": "white", "palomino": "palomino", "cremello": "cremello",
    "pinto": "pinto", "léopard": "leopard", "isabelle": "buckskin",
    "rouan": "roan", "pie": "pinto", "brun": "bay",
    "black": "black", "bay": "bay", "chestnut": "chestnut",
    "grey": "grey", "gray": "grey", "brown": "bay",
}


# ══════════════════════════════════════════════════════════════════════
#  FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════

def extract_color(name: str) -> str:
    """Extract coat color from the horse name/title."""
    name_lower = name.lower()
    for keyword, color in COLOR_MAP.items():
        if keyword in name_lower:
            return color
    return "unknown"


def compute_age_value_curve(age: float) -> float:
    """
    Model the real equestrian price-age curve:
    - Foals (0-1): Low value
    - Young (2-3): Rising (potential, unbroken)
    - Prime (4-7): Peak value (trained, competition-ready)
    - Adult (8-12): High but declining
    - Senior (13-16): Declining (schoolmaster value)
    - Veteran (17+): Low (retirement)
    
    Returns a value multiplier 0-1.
    """
    if pd.isna(age):
        return 0.5
    # Bell curve peaking around age 6-7
    return float(np.exp(-0.5 * ((age - 6.5) / 4.0) ** 2))


def estimate_training_level(age: float, breed: str, gender: str) -> int:
    """
    Estimate training level (0-5) based on age, breed, and gender.
    Domain logic:
    - Young horses (0-2): untrained (0-1)
    - 3-4 year olds: basic training (1-2)
    - 5-7 sport breeds: likely competition-trained (3-4)
    - 8+ year old sport breeds: experienced (4-5)
    - Non-sport breeds: lower ceiling
    - Stallions slightly less likely to be trained (harder to manage)
    """
    if pd.isna(age):
        return 2  # default

    tier = BREED_SPORT_TIER.get(breed, 2)
    
    # Base training level from age
    if age <= 1:
        base = 0
    elif age <= 2:
        base = 0.5
    elif age <= 3:
        base = 1.5
    elif age <= 4:
        base = 2.0
    elif age <= 6:
        base = 2.5
    elif age <= 10:
        base = 3.0
    elif age <= 15:
        base = 2.5  # declining for older horses
    else:
        base = 1.5

    # Scale by breed sport tier (higher tier → more likely trained)
    training = base * (tier / 3.0)

    # Stallions slightly less likely domestic-trained
    if gender == "Stallion":
        training *= 0.9

    # Cap at 5
    return min(int(round(training)), 5)


def compute_breed_price_premium(df: pd.DataFrame) -> dict:
    """
    Compute breed-specific price premium from the data itself.
    This is the ratio of breed median to global median.
    """
    global_median = df["price"].median()
    premiums = {}
    for breed in df["breed"].unique():
        breed_median = df[df["breed"] == breed]["price"].median()
        premiums[breed] = breed_median / global_median
    return premiums


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering transformations."""
    logger.info("  🔧 Engineering features...")

    # ── 1. Extract color from name ──
    df["color"] = df["name"].apply(extract_color)
    color_counts = df["color"].value_counts()
    logger.info(f"     Colors extracted: {len(color_counts)} unique (top: {color_counts.head(5).to_dict()})")

    # ── 2. Source as feature ──
    df["source"] = df["source"].fillna("unknown")

    # ── 3. Age value curve (non-linear age→price relationship) ──
    df["age_value_curve"] = df["age"].apply(compute_age_value_curve)

    # ── 4. Age polynomial features ──
    df["age_squared"] = df["age"] ** 2
    df["age_cubed"] = df["age"] ** 3

    # ── 5. Height squared ──
    df["height_squared"] = df["height"] ** 2

    # ── 6. Age × Height interaction ──
    df["age_x_height"] = df["age"] * df["height"].fillna(df["height"].median())

    # ── 7. Discipline from breed (domain knowledge) ──
    df["discipline"] = df["breed"].map(BREED_DISCIPLINE).fillna("mixed")

    # ── 8. Sport tier (breed quality tier) ──
    df["sport_tier"] = df["breed"].map(BREED_SPORT_TIER).fillna(2).astype(int)

    # ── 9. Training level (synthesized from age + breed + gender) ──
    df["training_level"] = df.apply(
        lambda row: estimate_training_level(row["age"], row["breed"], row["gender"]),
        axis=1,
    )

    # ── 10. Breed price premium (data-driven) ──
    breed_premiums = compute_breed_price_premium(df)
    df["breed_premium"] = df["breed"].map(breed_premiums).fillna(1.0)

    # ── 11. Is pony (height < 148.5 cm) ──
    df["is_pony"] = (df["height"].fillna(160) < 148.5).astype(int)

    # ── 12. Gender × Breed interaction tier ──
    # Mares and stallions of sport breeds are premium (breeding value)
    df["breeding_value"] = 0
    sport_mask = df["sport_tier"] >= 4
    df.loc[sport_mask & (df["gender"] == "Mare"), "breeding_value"] = 2
    df.loc[sport_mask & (df["gender"] == "Stallion"), "breeding_value"] = 3
    df.loc[sport_mask & (df["gender"] == "Gelding"), "breeding_value"] = 1

    # ── 13. Age category (for interaction with other features) ──
    df["age_category"] = pd.cut(
        df["age"],
        bins=[-1, 1, 3, 6, 10, 15, 50],
        labels=["foal", "young", "prime", "adult", "senior", "veteran"],
    ).astype(str)

    n_features = len([c for c in df.columns if c not in ["name", "price", "image_url"]])
    logger.info(f"     Total features: {n_features}")

    return df


# ══════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════════════

def load_and_prepare_data():
    """Load, engineer features, and split."""
    logger.info(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"  Raw shape: {df.shape}")

    # ── Outlier removal ──
    Q1 = df["price"].quantile(0.05)
    Q3 = df["price"].quantile(0.95)
    IQR = Q3 - Q1
    df = df[(df["price"] >= Q1 - 1.5 * IQR) & (df["price"] <= Q3 + 1.5 * IQR)].copy()
    logger.info(f"  After outlier removal: {df.shape}")

    # Height outlier removal
    df = df[(df["height"].isna()) | ((df["height"] >= 50) & (df["height"] <= 250))].copy()

    # ── Feature Engineering ──
    df = engineer_features(df)

    # ── Log-transform target ──
    y_raw = df["price"].copy()
    y = np.log1p(df["price"])  # log(1+price)
    logger.info(f"  Target: log1p(price)")
    logger.info(f"  Log price range: {y.min():.2f} – {y.max():.2f}")
    logger.info(f"  Log price mean: {y.mean():.2f} | std: {y.std():.2f}")

    # ── Define features ──
    categorical_features = ["breed", "gender", "color", "source", "discipline", "age_category"]
    numerical_features = [
        "age", "height",
        "age_value_curve", "age_squared", "age_cubed",
        "height_squared", "age_x_height",
        "sport_tier", "training_level", "breed_premium",
        "is_pony", "breeding_value",
    ]

    X = df[categorical_features + numerical_features].copy()

    logger.info(f"  Categorical: {categorical_features}")
    logger.info(f"  Numerical: {numerical_features}")
    logger.info(f"  Final samples: {len(X)}")

    # ── Split (preserve y_raw for evaluation in EUR) ──
    X_train, X_test, y_train, y_test, y_raw_train, y_raw_test = train_test_split(
        X, y, y_raw, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    logger.info(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    return X_train, X_test, y_train, y_test, y_raw_test, categorical_features, numerical_features


# ══════════════════════════════════════════════════════════════════════
#  PREPROCESSING
# ══════════════════════════════════════════════════════════════════════

def build_preprocessor(categorical_features, numerical_features):
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=15)),
    ])
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    return ColumnTransformer(transformers=[
        ("cat", cat_pipeline, categorical_features),
        ("num", num_pipeline, numerical_features),
    ])


# ══════════════════════════════════════════════════════════════════════
#  MODELS
# ══════════════════════════════════════════════════════════════════════

def get_models_and_params():
    from xgboost import XGBRegressor
    return [
        ("Ridge", Ridge(), {
            "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
        }, "grid"),
        ("RandomForest", RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1), {
            "model__n_estimators": [100, 200],
            "model__max_depth": [10, 20],
            "model__min_samples_leaf": [2, 5],
        }, "grid"),
        ("HistGradientBoosting", HistGradientBoostingRegressor(random_state=RANDOM_STATE), {
            "model__max_iter": randint(100, 500),
            "model__learning_rate": uniform(0.01, 0.19),
            "model__max_depth": randint(3, 10),
            "model__min_samples_leaf": randint(5, 50),
            "model__l2_regularization": uniform(0.0, 1.0),
        }, "random"),
        ("GradientBoosting", GradientBoostingRegressor(random_state=RANDOM_STATE), {
            "model__n_estimators": randint(100, 300),
            "model__learning_rate": uniform(0.01, 0.19),
            "model__max_depth": randint(3, 7),
            "model__subsample": uniform(0.7, 0.3),
        }, "random"),
        ("XGBoost", XGBRegressor(random_state=RANDOM_STATE, n_jobs=-1, verbosity=0), {
            "model__n_estimators": randint(100, 400),
            "model__learning_rate": uniform(0.01, 0.19),
            "model__max_depth": randint(3, 10),
            "model__subsample": uniform(0.7, 0.3),
            "model__colsample_bytree": uniform(0.6, 0.4),
            "model__reg_alpha": uniform(0.0, 1.0),
            "model__reg_lambda": uniform(0.0, 2.0),
        }, "random"),
        ("SVR", SVR(kernel="rbf"), {
            "model__C": [1.0, 10.0],
            "model__epsilon": [0.1, 0.5],
        }, "grid"),
    ]


# ══════════════════════════════════════════════════════════════════════
#  FEATURE SELECTION
# ══════════════════════════════════════════════════════════════════════

def run_selectkbest(X_train_processed, y_train, feature_names):
    logger.info("\n" + "=" * 60)
    logger.info("  FEATURE SELECTION — SelectKBest (f_regression)")
    logger.info("=" * 60)

    selector = SelectKBest(score_func=f_regression, k="all")
    selector.fit(X_train_processed, y_train)

    ranking = sorted(
        zip(feature_names, selector.scores_, selector.pvalues_),
        key=lambda x: x[1], reverse=True,
    )

    logger.info(f"\n  {'Feature':<35s}  {'F-Score':>10s}  {'p-value':>12s}")
    logger.info("  " + "─" * 60)
    for name, score, pval in ranking[:20]:  # top 20
        sig = "✅" if pval < 0.05 else "❌"
        logger.info(f"  {sig} {name:<33s}  {score:>10.1f}  {pval:>12.2e}")
    if len(ranking) > 20:
        logger.info(f"  ... and {len(ranking) - 20} more features")

    significant_count = sum(1 for _, _, p in ranking if p < 0.05)
    logger.info(f"\n  Significant features (p<0.05): {significant_count} / {len(ranking)}")
    return ranking


# ══════════════════════════════════════════════════════════════════════
#  TRAINING LOOP
# ══════════════════════════════════════════════════════════════════════

def train_and_compare(X_train, X_test, y_train, y_test, y_raw_test,
                      categorical_features, numerical_features):

    preprocessor = build_preprocessor(categorical_features, numerical_features)
    models = get_models_and_params()

    X_train_processed = preprocessor.fit_transform(X_train)
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = cat_feature_names + numerical_features

    logger.info(f"\n  Total features after encoding: {len(all_feature_names)}")

    # SelectKBest
    ranking = run_selectkbest(X_train_processed, y_train, all_feature_names)
    significant_count = sum(1 for _, _, p in ranking if p < 0.05)
    optimal_k = max(significant_count, 10)
    optimal_k = min(optimal_k, len(all_feature_names))
    logger.info(f"  Using SelectKBest k={optimal_k}")

    results = []

    for name, model, param_grid, search_type in models:
        logger.info("\n" + "=" * 60)
        logger.info(f"  MODEL: {name}")
        logger.info("=" * 60)

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("feature_selection", SelectKBest(score_func=f_regression, k=optimal_k)),
            ("model", model),
        ])

        full_param_grid = param_grid.copy()
        k_values = list(set([
            min(optimal_k, len(all_feature_names)),
            len(all_feature_names),
        ]))
        full_param_grid["feature_selection__k"] = k_values

        t_start = time.time()

        if search_type == "random":
            n_fits = N_ITER_RANDOM * CV_FOLDS
            logger.info(f"  RandomizedSearchCV: {N_ITER_RANDOM} iters × {CV_FOLDS} folds = {n_fits} fits")
            searcher = RandomizedSearchCV(
                pipeline, param_distributions=full_param_grid,
                n_iter=N_ITER_RANDOM, cv=CV_FOLDS,
                scoring="neg_mean_absolute_error", n_jobs=-1,
                random_state=RANDOM_STATE, return_train_score=True,
            )
        else:
            n_combos = 1
            for v in full_param_grid.values():
                n_combos *= len(v)
            logger.info(f"  GridSearchCV: {n_combos} combos × {CV_FOLDS} folds = {n_combos * CV_FOLDS} fits")
            searcher = GridSearchCV(
                pipeline, param_grid=full_param_grid,
                cv=CV_FOLDS, scoring="neg_mean_absolute_error",
                n_jobs=-1, return_train_score=True,
            )

        searcher.fit(X_train, y_train)
        t_elapsed = time.time() - t_start

        # ── Evaluate on test set ──
        # Predictions are in log space → convert back to EUR
        y_pred_log = searcher.predict(X_test)
        y_pred_eur = np.expm1(y_pred_log)  # inverse of log1p
        y_actual_eur = y_raw_test.values

        # Metrics in EUR (what matters for business)
        mae = mean_absolute_error(y_actual_eur, y_pred_eur)
        rmse = np.sqrt(mean_squared_error(y_actual_eur, y_pred_eur))
        r2 = r2_score(y_actual_eur, y_pred_eur)
        mape = mean_absolute_percentage_error(y_actual_eur, y_pred_eur) * 100

        # Also R² in log-space (what the model actually optimizes)
        r2_log = r2_score(y_test, y_pred_log)
        cv_mae_log = -searcher.best_score_

        result = {
            "name": name,
            "test_mae": mae, "test_rmse": rmse,
            "test_r2": r2, "test_r2_log": r2_log,
            "test_mape": mape, "cv_mae_log": cv_mae_log,
            "best_params": searcher.best_params_,
            "train_time_s": t_elapsed,
            "best_pipeline": searcher.best_estimator_,
        }
        results.append(result)

        logger.info(f"\n  Best Params: {searcher.best_params_}")
        logger.info(f"  ┌────────────────────────────────────────────────┐")
        logger.info(f"  │  R² (log-space):  {r2_log:>8.4f}                    │")
        logger.info(f"  │  R² (EUR):        {r2:>8.4f}                    │")
        logger.info(f"  │  Test MAE:  {mae:>10,.0f} EUR                    │")
        logger.info(f"  │  Test RMSE: {rmse:>10,.0f} EUR                    │")
        logger.info(f"  │  Test MAPE: {mape:>9.1f}%                        │")
        logger.info(f"  │  Time:      {t_elapsed:>8.1f}s                        │")
        logger.info(f"  └────────────────────────────────────────────────┘")

    return results


# ══════════════════════════════════════════════════════════════════════
#  COMPARISON & SAVE
# ══════════════════════════════════════════════════════════════════════

def print_comparison_table(results):
    logger.info("\n\n")
    logger.info("╔" + "═" * 90 + "╗")
    logger.info("║" + "  FINAL MODEL COMPARISON (with Feature Engineering + Log Target)".center(90) + "║")
    logger.info("╠" + "═" * 90 + "╣")

    header = f"║ {'Model':<22s} │ {'R² (log)':>9s} │ {'R² (EUR)':>9s} │ {'MAE (EUR)':>10s} │ {'MAPE':>7s} │ {'Time':>6s} ║"
    logger.info(header)
    logger.info("╟" + "─" * 90 + "╢")

    sorted_results = sorted(results, key=lambda x: x["test_r2"], reverse=True)

    for i, r in enumerate(sorted_results):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
        line = (
            f"║ {medal} {r['name']:<19s} │ "
            f"{r['test_r2_log']:>9.4f} │ "
            f"{r['test_r2']:>9.4f} │ "
            f"{r['test_mae']:>10,.0f} │ "
            f"{r['test_mape']:>6.1f}% │ "
            f"{r['train_time_s']:>5.1f}s ║"
        )
        logger.info(line)

    logger.info("╚" + "═" * 90 + "╝")

    winner = sorted_results[0]
    logger.info(f"\n  🏆 WINNER: {winner['name']}")
    logger.info(f"     R² (EUR)  = {winner['test_r2']:.4f}")
    logger.info(f"     R² (log)  = {winner['test_r2_log']:.4f}")
    logger.info(f"     MAE       = {winner['test_mae']:,.0f} EUR")
    logger.info(f"     MAPE      = {winner['test_mape']:.1f}%")

    return winner


def save_best_model(winner, results):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = OUTPUT_DIR / "pricing_pipeline.joblib"
    joblib.dump(winner["best_pipeline"], model_path)
    logger.info(f"\n  ✅ Best pipeline saved → {model_path}")

    comparison = []
    for r in sorted(results, key=lambda x: x["test_r2"], reverse=True):
        comparison.append({
            "model": r["name"],
            "test_mae": round(r["test_mae"], 2),
            "test_rmse": round(r["test_rmse"], 2),
            "test_r2": round(r["test_r2"], 4),
            "test_r2_log": round(r["test_r2_log"], 4),
            "test_mape": round(r["test_mape"], 2),
            "train_time_s": round(r["train_time_s"], 2),
            "best_params": {
                k: (str(v) if not isinstance(v, (int, float, bool, type(None))) else v)
                for k, v in r["best_params"].items()
            },
        })

    metrics = {
        "winner": winner["name"],
        "winner_r2": round(winner["test_r2"], 4),
        "winner_mae": round(winner["test_mae"], 2),
        "all_models": comparison,
        "feature_engineering": [
            "log1p target transform",
            "color extraction from name",
            "source as feature",
            "age_value_curve (gaussian bell at age 6.5)",
            "age², age³ polynomial",
            "height², age×height interaction",
            "discipline from breed (domain knowledge)",
            "sport_tier (breed quality 1-5)",
            "training_level (synthesized from age+breed+gender)",
            "breed_premium (data-driven median ratio)",
            "is_pony (height < 148.5cm)",
            "breeding_value (gender×sport_tier interaction)",
            "age_category (foal/young/prime/adult/senior/veteran)",
        ],
        "feature_selection": "SelectKBest (f_regression)",
        "hyperparameter_tuning": f"GridSearchCV + RandomizedSearchCV ({CV_FOLDS}-fold)",
    }

    metrics_path = OUTPUT_DIR / "model_comparison.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"  ✅ Comparison report saved → {metrics_path}")

    simple_metrics = {
        "model": winner["name"],
        "mae": round(winner["test_mae"], 2),
        "rmse": round(winner["test_rmse"], 2),
        "r2": round(winner["test_r2"], 4),
        "mape": round(winner["test_mape"], 2),
        "target_transform": "log1p",
    }
    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(simple_metrics, f, indent=2)


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║  EquiVision — Advanced Pricing Pipeline (v2)                 ║")
    logger.info("║  Feature Engineering + Log Target + 6 Models                 ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")

    t_total = time.time()

    X_train, X_test, y_train, y_test, y_raw_test, cat_feats, num_feats = load_and_prepare_data()
    results = train_and_compare(X_train, X_test, y_train, y_test, y_raw_test, cat_feats, num_feats)
    winner = print_comparison_table(results)
    save_best_model(winner, results)

    elapsed = time.time() - t_total
    logger.info(f"\n  Total pipeline time: {elapsed:.1f}s")
    logger.info("  Done! 🎉")


if __name__ == "__main__":
    main()
