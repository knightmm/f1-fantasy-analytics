from scripts.fetch_assets import main as fetch_assets
from scripts.prepare_assets import main as prepare_assets
from scripts.fetch_teams import main as fetch_teams
from scripts.prepare_teams import main as prepare_teams
from scripts.fetch_detailed_teams import main as fetch_detailed_teams
from scripts.prepare_detailed_teams import main as prepare_detailed_teams
from scripts.load_to_database import main as load_to_database
from scripts.build_marts import main as build_marts


def run_pipeline():
    print("Starting F1 Fantasy pipeline...")

    print("1. Fetching public asset data...")
    fetch_assets()

    print("2. Preparing asset data...")
    prepare_assets()

    print("3. Fetching public team data...")
    fetch_teams()

    print("4. Preparing team data...")
    prepare_teams()

    print("5. Fetching detailed team data...")
    fetch_detailed_teams()

    print("6. Preparing detailed team data...")
    prepare_detailed_teams()

    print("7. Loading and validating database...")
    load_to_database()

    print("8. Creating marts...")
    build_marts()

    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()