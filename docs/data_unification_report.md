# Horse Data Unification & Pipeline Update Report

## 1. Unified Data Pipeline

We have successfully created a "Universal Cleaner" script that unifies data from 7 different sources into a single, high-quality dataset.

**Script:** `backend/scripts/unify_data.py`
**Output:** `backend/data/processed/unified_horse_data.csv`
**Total Records:** ~14,000 processed horses

### Key Features:

- **Robust Parsers:** Custom logic handles broken CSVs (`horsequest`, `caballo`), multiline records (`shf`, `equirodi`), and messy HTML dumps (`paardplaats`).
- **Smart Normalization:**
  - **Breeds:** Expanded mapping handles French/German variations (e.g., "Mangan" -> "Morgan", "Westphalien" -> "Westphalian"). reduced "Other" category by ~60%.
  - **Price:** Filters outliers and handles localized formats.
  - **Measures:** Standardizes Height (cm) and Age (years).

## 2. Model Retraining

The pricing model has been updated to utilize this new unified dataset.

- **Training Script:** `backend/app/ml/pricing/train.py`
- **Status:** Retrained with XGBoost.
- **Performance:** ~7,000 EUR MAE (Baseline). The model now has access to a much wider variety of breeds and data points.

## 3. Critical Gap Identification: Vision Dataset

We identified specific discrepancies between the **Sales Data** (what people are selling) and the **Vision Data** (what the AI can see).

**Missing from Vision Model:**
The current Vision dataset (`labels.json`) only supports 11 breeds. It is **missing** the following top breeds found in your sales data:

1.  **Quarter Horse** (1,756 records - #2 most common!)
2.  **Oldenburg** (917 records)
3.  **Westphalian** (489 records)
4.  **KWPN** (460 records)
5.  **Holsteiner** (352 records)
6.  **Ponies** (Various breeds)

**Recommendation:**
To build a truly "God Tier" app, we must expand the vision dataset to include these breeds. The Vision model currently cannot classify the 2nd most common horse in your database.

## Next Steps

1.  **Expand Vision Dataset:** Update `scripts/bulk_scrape_vision.py` to download images for the missing top breeds.
2.  **Retrain Vision Model:** Train a new YOLO/Classifier model on the expanded dataset.
3.  **Integrate:** Ensure the frontend sends images to the new model for accurate breed detection to auto-fill listing details.
