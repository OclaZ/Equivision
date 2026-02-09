
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_pricing_model(data_path, output_dir):
    """
    Create a simple rule-based pricing model as a placeholder
    until we can resolve the numpy/pandas installation issues.
    """
    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Creating simple rule-based pricing model...")
    
    # Load raw data
    with open(data_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Simple price extraction and statistics
    prices = []
    for item in raw_data:
        price_str = item.get('price', '')
        if price_str and 'demande' not in price_str.lower() and 'N/A' not in price_str:
            # Extract numeric value
            clean_price = ''.join(c for c in price_str if c.isdigit())
            if clean_price:
                prices.append(float(clean_price))
    
    if not prices:
        logger.error("No valid prices found in data")
        return
    
    # Calculate statistics
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    logger.info(f"Price Statistics:")
    logger.info(f"  Count: {len(prices)}")
    logger.info(f"  Average: {avg_price:.2f} DH")
    logger.info(f"  Min: {min_price:.2f} DH")
    logger.info(f"  Max: {max_price:.2f} DH")
    
    # Save model metadata
    model_info = {
        "type": "rule_based",
        "version": "1.0",
        "statistics": {
            "count": len(prices),
            "average": avg_price,
            "min": min_price,
            "max": max_price
        },
        "note": "Placeholder model - will be replaced with XGBoost once dependency issues are resolved"
    }
    
    with open(output_dir / "model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)
    
    logger.info(f"Model info saved to {output_dir / 'model_info.json'}")

if __name__ == "__main__":
    DATA_PATH = "d:/EquiVision/backend/data/raw/avito_horses.json"
    OUTPUT_DIR = "d:/EquiVision/backend/app/ml/pricing/weights"
    
    if Path(DATA_PATH).exists():
        create_simple_pricing_model(DATA_PATH, OUTPUT_DIR)
    else:
        logger.error(f"Data file not found at {DATA_PATH}")
