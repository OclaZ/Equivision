"""
╔══════════════════════════════════════════════════════════════════════╗
║  EquiVision — Pricing Model Comparison Pipeline                     ║
║  4 Scikit-Learn Models × GridSearchCV × SelectKBest                 ║
║                                                                      ║
║  Models:                                                             ║
║    1. Ridge Regression          (linear baseline)                    ║
║    2. Random Forest Regressor   (bagging ensemble)                   ║
║    3. Gradient Boosting Regressor (boosting ensemble)                ║
║    4. SVR                       (kernel-based)                       ║
║                                                                      ║
║  Output: best model saved as pricing_pipeline.joblib                 ║
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
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
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


def load_and_prepare_data():
    """Load, clean, and split the unified horse pricing dataset."""
    logger.info(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"  Raw shape: {df.shape}")

    # ── Outlier removal (IQR method on price) ──
    Q1 = df["price"].quantile(0.05)
    Q3 = df["price"].quantile(0.95)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    df = df[(df["price"] >= lower) & (df["price"] <= upper)].copy()
    logger.info(f"  After outlier removal (5-95 IQR): {df.shape}")

    # ── Height outlier removal ──
    df = df[(df["height"].isna()) | ((df["height"] >= 50) & (df["height"] <= 250))].copy()

    # ── Feature & target definition ──
    categorical_features = ["breed", "gender"]
    numerical_features = ["age", "height"]
    target = "price"

    X = df[categorical_features + numerical_features].copy()
    y = df[target].copy()

    logger.info(f"  Features: {categorical_features + numerical_features}")
    logger.info(f"  Target: {target}")
    logger.info(f"  Final samples: {len(X)}")
    logger.info(f"  Price range: {y.min():,.0f} – {y.max():,.0f} EUR")
    logger.info(f"  Price mean: {y.mean():,.0f} EUR | median: {y.median():,.0f} EUR")

    # ── Split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    logger.info(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    return X_train, X_test, y_train, y_test, categorical_features, numerical_features


def build_preprocessor(categorical_features, numerical_features):
    """Build the sklearn ColumnTransformer for mixed feature types."""

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=20)),
    ])

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", cat_pipeline, categorical_features),
            ("num", num_pipeline, numerical_features),
        ]
    )
    return preprocessor


def get_models_and_params():
    """
    Define the 4 scikit-learn models with their GridSearchCV parameter grids.
    Each entry: (name, model, param_grid)
    """
    models = [
        # ─── 1. Ridge Regression (linear baseline) ───
        (
            "Ridge",
            Ridge(),
            {
                "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
            },
        ),
        # ─── 2. Random Forest Regressor (bagging) ───
        (
            "RandomForest",
            RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1),
            {
                "model__n_estimators": [100, 200, 300],
                "model__max_depth": [10, 20, None],
                "model__min_samples_split": [2, 5],
                "model__min_samples_leaf": [1, 2],
            },
        ),
        # ─── 3. Gradient Boosting Regressor (boosting) ───
        (
            "GradientBoosting",
            GradientBoostingRegressor(random_state=RANDOM_STATE),
            {
                "model__n_estimators": [100, 200, 300],
                "model__learning_rate": [0.01, 0.05, 0.1],
                "model__max_depth": [3, 5, 7],
                "model__subsample": [0.8, 1.0],
            },
        ),
        # ─── 4. SVR (kernel-based) ───
        (
            "SVR",
            SVR(),
            {
                "model__C": [0.1, 1.0, 10.0, 100.0],
                "model__epsilon": [0.01, 0.1, 0.5],
                "model__kernel": ["rbf", "linear"],
            },
        ),
    ]
    return models


def run_selectkbest(X_train_processed, y_train, feature_names):
    """Run SelectKBest to rank features by importance."""
    logger.info("\n" + "=" * 60)
    logger.info("  FEATURE SELECTION — SelectKBest (f_regression)")
    logger.info("=" * 60)

    selector = SelectKBest(score_func=f_regression, k="all")
    selector.fit(X_train_processed, y_train)

    scores = selector.scores_
    pvalues = selector.pvalues_

    # Build ranking table
    ranking = sorted(
        zip(feature_names, scores, pvalues),
        key=lambda x: x[1],
        reverse=True,
    )

    logger.info(f"\n  {'Feature':<30s}  {'F-Score':>10s}  {'p-value':>12s}  {'Significant':>11s}")
    logger.info("  " + "─" * 67)
    for name, score, pval in ranking:
        sig = "✅ Yes" if pval < 0.05 else "❌ No"
        logger.info(f"  {name:<30s}  {score:>10.2f}  {pval:>12.2e}  {sig:>11s}")

    # Also try mutual_info
    logger.info("\n  SelectKBest — mutual_info_regression:")
    mi_selector = SelectKBest(score_func=mutual_info_regression, k="all")
    mi_selector.fit(X_train_processed, y_train)
    mi_scores = mi_selector.scores_

    mi_ranking = sorted(
        zip(feature_names, mi_scores),
        key=lambda x: x[1],
        reverse=True,
    )
    logger.info(f"\n  {'Feature':<30s}  {'MI Score':>10s}")
    logger.info("  " + "─" * 42)
    for name, score in mi_ranking:
        logger.info(f"  {name:<30s}  {score:>10.4f}")

    return ranking, mi_ranking


def train_and_compare(X_train, X_test, y_train, y_test, categorical_features, numerical_features):
    """Train all 4 models with GridSearchCV and compare."""

    preprocessor = build_preprocessor(categorical_features, numerical_features)
    models = get_models_and_params()

    # ── Pre-fit the preprocessor to get feature names for SelectKBest ──
    X_train_processed = preprocessor.fit_transform(X_train)

    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = cat_feature_names + numerical_features

    logger.info(f"\n  Total features after encoding: {len(all_feature_names)}")

    # ── SelectKBest Analysis ──
    f_ranking, mi_ranking = run_selectkbest(X_train_processed, y_train, all_feature_names)

    # Determine optimal k (features with p < 0.05)
    significant_count = sum(1 for _, _, p in f_ranking if p < 0.05)
    optimal_k = max(significant_count, 4)  # At least 4 features
    optimal_k = min(optimal_k, len(all_feature_names))  # Can't exceed total
    logger.info(f"\n  Significant features (p<0.05): {significant_count}")
    logger.info(f"  Using SelectKBest k={optimal_k}")

    # ── Train each model ──
    results = []

    for name, model, param_grid in models:
        logger.info("\n" + "=" * 60)
        logger.info(f"  MODEL: {name}")
        logger.info("=" * 60)

        # Build full pipeline: preprocessor → selectkbest → model
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("feature_selection", SelectKBest(score_func=f_regression, k=optimal_k)),
            ("model", model),
        ])

        # Prefix param grid keys are already correct (model__)
        # Add SelectKBest k to the grid too
        full_param_grid = param_grid.copy()
        full_param_grid["feature_selection__k"] = [
            min(optimal_k, len(all_feature_names)),
            min(optimal_k + 5, len(all_feature_names)),
            len(all_feature_names),  # "all" equivalent
        ]
        # Remove duplicates from the k list
        full_param_grid["feature_selection__k"] = list(
            set(full_param_grid["feature_selection__k"])
        )

        n_combos = 1
        for v in full_param_grid.values():
            n_combos *= len(v)
        logger.info(f"  Grid: {n_combos} combinations × {CV_FOLDS} folds = {n_combos * CV_FOLDS} fits")

        t_start = time.time()

        grid_search = GridSearchCV(
            pipeline,
            param_grid=full_param_grid,
            cv=CV_FOLDS,
            scoring="neg_mean_absolute_error",
            n_jobs=-1,
            verbose=0,
            return_train_score=True,
        )
        grid_search.fit(X_train, y_train)

        t_elapsed = time.time() - t_start

        # ── Evaluation on test set ──
        y_pred = grid_search.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100

        # CV score
        cv_mae = -grid_search.best_score_

        result = {
            "name": name,
            "test_mae": mae,
            "test_rmse": rmse,
            "test_r2": r2,
            "test_mape": mape,
            "cv_mae": cv_mae,
            "best_params": grid_search.best_params_,
            "train_time_s": t_elapsed,
            "best_pipeline": grid_search.best_estimator_,
        }
        results.append(result)

        logger.info(f"\n  Best Params: {grid_search.best_params_}")
        logger.info(f"  ┌──────────────────────────────────────────┐")
        logger.info(f"  │  CV  MAE:  {cv_mae:>10,.2f} EUR              │")
        logger.info(f"  │  Test MAE: {mae:>10,.2f} EUR              │")
        logger.info(f"  │  Test RMSE:{rmse:>10,.2f} EUR              │")
        logger.info(f"  │  Test R²:  {r2:>10.4f}                   │")
        logger.info(f"  │  Test MAPE:{mape:>9.1f}%                   │")
        logger.info(f"  │  Time:     {t_elapsed:>8.1f}s                   │")
        logger.info(f"  └──────────────────────────────────────────┘")

    return results


def print_comparison_table(results):
    """Print a final comparison table and declare the winner."""
    logger.info("\n\n")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + "  FINAL MODEL COMPARISON".center(78) + "║")
    logger.info("╠" + "═" * 78 + "╣")

    header = f"║ {'Model':<22s} │ {'CV MAE':>10s} │ {'Test MAE':>10s} │ {'Test R²':>8s} │ {'MAPE':>7s} │ {'Time':>6s} ║"
    logger.info(header)
    logger.info("╟" + "─" * 78 + "╢")

    # Sort by test MAE (lower is better)
    sorted_results = sorted(results, key=lambda x: x["test_mae"])

    for i, r in enumerate(sorted_results):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
        line = (
            f"║ {medal} {r['name']:<19s} │ "
            f"{r['cv_mae']:>10,.0f} │ "
            f"{r['test_mae']:>10,.0f} │ "
            f"{r['test_r2']:>8.4f} │ "
            f"{r['test_mape']:>6.1f}% │ "
            f"{r['train_time_s']:>5.1f}s ║"
        )
        logger.info(line)

    logger.info("╚" + "═" * 78 + "╝")

    winner = sorted_results[0]
    logger.info(f"\n  🏆 WINNER: {winner['name']}")
    logger.info(f"     MAE  = {winner['test_mae']:,.2f} EUR")
    logger.info(f"     R²   = {winner['test_r2']:.4f}")
    logger.info(f"     MAPE = {winner['test_mape']:.1f}%")
    logger.info(f"     Params: {winner['best_params']}")

    return winner


def save_best_model(winner, results):
    """Save the best model pipeline and all metrics."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save the best pipeline
    model_path = OUTPUT_DIR / "pricing_pipeline.joblib"
    joblib.dump(winner["best_pipeline"], model_path)
    logger.info(f"\n  ✅ Best pipeline saved → {model_path}")

    # Save comparison metrics
    comparison = []
    for r in sorted(results, key=lambda x: x["test_mae"]):
        comparison.append({
            "model": r["name"],
            "cv_mae": round(r["cv_mae"], 2),
            "test_mae": round(r["test_mae"], 2),
            "test_rmse": round(r["test_rmse"], 2),
            "test_r2": round(r["test_r2"], 4),
            "test_mape": round(r["test_mape"], 2),
            "train_time_s": round(r["train_time_s"], 2),
            "best_params": {
                k: (str(v) if not isinstance(v, (int, float, bool, type(None))) else v)
                for k, v in r["best_params"].items()
            },
        })

    metrics = {
        "winner": winner["name"],
        "winner_mae": round(winner["test_mae"], 2),
        "winner_r2": round(winner["test_r2"], 4),
        "all_models": comparison,
        "feature_selection": "SelectKBest (f_regression)",
        "hyperparameter_tuning": f"GridSearchCV ({CV_FOLDS}-fold)",
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
    }

    metrics_path = OUTPUT_DIR / "model_comparison.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"  ✅ Comparison report saved → {metrics_path}")

    # Also save simplified metrics.json for backward compat
    simple_metrics = {
        "model": winner["name"],
        "mae": round(winner["test_mae"], 2),
        "rmse": round(winner["test_rmse"], 2),
        "r2": round(winner["test_r2"], 4),
        "mape": round(winner["test_mape"], 2),
    }
    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(simple_metrics, f, indent=2)


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║  EquiVision — Pricing Model Comparison Pipeline          ║")
    logger.info("║  4 Models × GridSearchCV × SelectKBest                   ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    t_total = time.time()

    # 1. Load data
    X_train, X_test, y_train, y_test, cat_feats, num_feats = load_and_prepare_data()

    # 2. Train & compare all 4 models
    results = train_and_compare(X_train, X_test, y_train, y_test, cat_feats, num_feats)

    # 3. Print comparison table
    winner = print_comparison_table(results)

    # 4. Save best model
    save_best_model(winner, results)

    elapsed = time.time() - t_total
    logger.info(f"\n  Total pipeline time: {elapsed:.1f}s")
    logger.info("  Done! 🎉")


if __name__ == "__main__":
    main()
