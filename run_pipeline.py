from scripts.fetch_assets import main as fetch_assets
from scripts.fetch_league_results import main as fetch_league_results
from scripts.load_to_database import main as load_to_database
from scripts.build_marts import main as build_marts

def run_pipeline():
    print("Starting F1 Fantasy pipeline...")

    print("1. Fetching asset data...")
    fetch_assets()

    print("2. Fetching league data...")
    fetch_league_results()

    print("3. Loading data to database...")
    load_to_database()

    print("4. Creating marts...")
    build_marts()

    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()   