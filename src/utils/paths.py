import os
import json

# Season-level datasets
def get_season_processed_file_path(dataset_name, season):
    return os.path.join(
        "data",
        "processed",
        f"{dataset_name}_{season}.csv"
    )

# Race-level datasets
def get_raw_file_path(dataset_name, race_number):
    return os.path.join(
        "data",
        "raw",
        f"{dataset_name}_race_{race_number}.json"
    )


def raw_file_exists(dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)
    return os.path.exists(file_path)


def load_raw_json(dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)

    with open(file_path, "r") as f:
        return json.load(f)


def save_raw_json(data, dataset_name, race_number):
    file_path = get_raw_file_path(dataset_name, race_number)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def get_processed_file_path(dataset_name, race_number):
    return os.path.join(
        "data",
        "processed",
        f"{dataset_name}_race_{race_number}.csv"
    )


def save_processed_csv(data, dataset_name, race_number):
    file_path = get_processed_file_path(dataset_name, race_number)
    data.to_csv(file_path, index=False)


# Detailed team datasets (league member + team + race)
def get_detailed_team_raw_path(user_guid, team_no, race_number):
    return os.path.join(
        "data",
        "raw",
        "detailed_teams",
        f"{user_guid}_team_{team_no}_race_{race_number}.json"
    )


def detailed_team_raw_exists(user_guid, team_no, race_number):
    file_path = get_detailed_team_raw_path(
        user_guid,
        team_no,
        race_number
    )
    return os.path.exists(file_path)


def load_detailed_team_raw(user_guid, team_no, race_number):
    file_path = get_detailed_team_raw_path(
        user_guid,
        team_no,
        race_number
    )

    with open(file_path, "r") as f:
        return json.load(f)


def save_detailed_team_raw(data, user_guid, team_no, race_number):
    file_path = get_detailed_team_raw_path(
        user_guid,
        team_no,
        race_number
    )

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)