# F1 Fantasy Analytics

A data analytics project for exploring F1 Fantasy league performance in more detail than is available through the official application interface.

The project uses data available through F1 Fantasy to reconstruct league and team history and make calculations that would otherwise require manual work. This includes analysis of team value and value growth, chip usage, transfers, team composition and race-by-race performance.

## Pipeline overview

The project follows a simple data pipeline:

**F1 Fantasy API → raw JSON → processed data → SQLite → analytical marts → FastAPI → Streamlit**

Raw API responses are preserved before transformation. Cleaned datasets are loaded into SQLite, where SQL marts prepare the data used by the API and analytics application.

## Data collection architecture

The project combines public F1 Fantasy league data with authenticated opponent-team endpoints.

Public league standings are used to identify the team entered by each league member and provide:

- user identifier
- team number
- league rank
- race points
- team composition

These identifiers are then used to request richer historical team data from the authenticated opponent-team endpoint, including:

- captain selection
- team value and remaining budget
- substitutions
- chip usage
- overall rank and points

The collected raw JSON is preserved before transformation and loading into SQLite.

## Project structure

```text
f1-fantasy-analytics/
├── app/
│   ├── Home.py
│   ├── api.py
│   └── pages/
├── data/
│   ├── raw/
│   ├── processed/
│   └── reference/
├── notebooks/
├── scripts/
├── sql/
├── src/
│   └── utils/
├── requirements.txt
└── run_pipeline.py
```

- **`scripts/`** — executable pipeline steps for fetching data, loading it into SQLite and building analytical marts.
- **`src/`** — reusable Python transformation logic used by the pipeline.
- **`src/utils/`** — shared utilities for paths, database access and race metadata.
- **`sql/`** — SQL transformations used to create analysis-ready marts.
- **`app/`** — FastAPI and Streamlit application code. Additional Streamlit views are stored in `app/pages/`.
- **`notebooks/`** — exploratory analysis and development work.

### Data layers

- **`data/raw/`** — original API responses stored as JSON.
- **`data/processed/`** — cleaned and structured datasets produced from the raw responses.
- **SQLite** — relational storage for processed data and analytical marts.
- **`data/reference/`** — version-controlled reference data such as race and Fantasy chip metadata.

Raw and processed data, local databases and private notebooks are excluded from Git.

## Installation

Python 3.11 is recommended.

Clone the repository:

    git clone https://github.com/knightmm/f1-fantasy-analytics.git
    cd f1-fantasy-analytics

Create and activate a virtual environment:

    python -m venv .venv
    source .venv/bin/activate

Install the project dependencies:

    pip install -r requirements.txt

Run the data pipeline:

    python run_pipeline.py

## Configuration

Some F1 Fantasy endpoints require authentication. Create a `.env` file in the project root:

    F1_COOKIE=your_cookie_here
    F1_USER_AGENT=your_user_agent_here
    LEAGUE_ID=your_league_id_here

The `.env` file and local data are excluded from Git.

## Running the application

Start the FastAPI application:

    fastapi dev app/api.py

Then, in a separate terminal, start the Streamlit application:

    streamlit run app/Home.py

The application currently runs locally.

## Analytics application

The Streamlit application provides interactive views of league and race performance. Further views are being developed to make use of the expanded historical team, value, transfer and chip data.