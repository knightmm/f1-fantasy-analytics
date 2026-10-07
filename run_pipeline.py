from scripts.fetch_assets import main as fetch_assets
from scripts.fetch_league_results import main as fetch_league_results
from scripts.fetch_detailed_teams import main as fetch_detailed_teams
from scripts.prepare_detailed_teams import main as prepare_detailed_teams
from scripts.load_to_database import main as load_to_database
from scripts.build_marts import main as build_marts


def run_pipeline():
    print("Starting F1 Fantasy pipeline...")

    print("1. Fetching public asset data...")
    fetch_assets()

    print("2. Fetching public team data...")
    fetch_league_results()

    print("3. Fetching detailed team data...")
    fetch_detailed_teams()

    print("4. Preparing detailed team data...")
    prepare_detailed_teams()

    print("5. Loading data to database...")
    load_to_database()

    print("6. Creating marts...")
    build_marts()

    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()