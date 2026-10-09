# F1 Fantasy Analytics

A data analytics project for exploring F1 Fantasy league performance in more detail than is available through the official application interface.

The project uses F1 Fantasy data to reconstruct league and team history and make comparisons that would otherwise require manual calculations. This includes team value and growth, chip usage, transfers, team composition and race-by-race performance.

The project is intended for personal analysis of leagues in which the user participates.

## Pipeline overview

The project separates data collection, preparation, database loading and analytical modelling.

```text
F1 Fantasy API (public + authenticated)
              ↓
     Data collection (JSON)
              ↓
     Data preparation (CSV)
              ↓
     SQLite source tables
       + data validation
              ↓
      SQL analytical marts
              ↓
            FastAPI
              ↓
           Streamlit
```

Raw API responses are preserved separately from processed datasets. The SQLite source tables retain the collected data, while analytical marts combine datasets and calculate additional metrics for the application.

## Data collection architecture

The project combines public F1 Fantasy league data with authenticated opponent-team endpoints.

Public league standings provide team identifiers, rankings, race points and selections. These identifiers are used to retrieve more detailed historical data, including captain selections, team finances, substitutions, chip usage and overall performance.

The authenticated data allows the project to analyse information that is available in F1 Fantasy but difficult to compare across teams and races using the official interface.

## Project structure

```text
f1-fantasy-analytics/
├── api/
│   └── main.py
├── app/
│   ├── Home.py
│   ├── config.py
│   └── pages/
│       ├── 1_League_Evolution.py
│       └── 2_Chip_Strategy.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── reference/
├── docs/
├── notebooks/
├── scripts/
├── sql/
├── src/
│   └── utils/
├── requirements.txt
└── run_pipeline.py
```

- **`scripts/`** — executable stages for data collection, preparation, database loading and mart creation.
- **`src/`** — reusable transformation and validation logic.
- **`src/utils/`** — shared utilities for paths, database access and race metadata.
- **`sql/`** — SQL transformations for analytical marts.
- **`api/`** — FastAPI endpoints exposing the analytical data.
- **`app/`** — Streamlit dashboard and additional analytical pages.
- **`notebooks/`** — exploratory analysis and development work.
- **`docs/`** — technical notes and supporting screenshots.

### Data layers

- **`data/raw/`** — original API responses stored as JSON.
- **`data/processed/`** — cleaned and structured CSV datasets.
- **SQLite** — relational source tables and analytical marts.
- **`data/reference/`** — version-controlled race and Fantasy chip metadata.

Raw and processed data, local databases and private notebooks are excluded from Git.

## Analytical marts

SQL marts prepare the datasets used by the API and dashboard.

The main team marts are:

- **`mart_team_race`** — historical team performance, cumulative points, finances, value changes and league averages.
- **`mart_team_chips`** — chip usage, availability and race performance, using each team's latest available snapshot.

Additional marts provide historical asset-price changes, latest asset information and enriched team selections.

### Historical team valuation

The F1 Fantasy API does not consistently provide historical team valuations. Missing values are reconstructed from team selections and race-specific asset prices.

The calculation accounts for Limitless and Final Fix exceptions and distinguishes API-recorded valuations from calculated values. This allows continuous comparisons of asset value, remaining cash and total team wealth across the current dataset.

## Installation

Python 3.11 is recommended.

Clone the repository:

```bash
git clone https://github.com/knightmm/f1-fantasy-analytics.git
cd f1-fantasy-analytics
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Some F1 Fantasy endpoints require authentication. Create a `.env` file in the project root:

```dotenv
F1_COOKIE=your_cookie_here
F1_USER_AGENT=your_user_agent_here
LEAGUE_ID=your_league_id_here

# Optional: show your own team's stats by default on the Home page
DEFAULT_TEAM="Your Team Name"
```

The `.env` file and local data are excluded from Git.

## Running the project

Run the complete data pipeline:

```bash
python run_pipeline.py
```

Start the FastAPI application:

```bash
fastapi dev api/main.py
```

Then, in a separate terminal, start Streamlit:

```bash
streamlit run app/Home.py
```

The application currently runs locally.

## Analytics application

The Streamlit dashboard currently includes three views:

- **Home** — latest league standings, team performance and financial comparisons.
- **League Evolution** — historical comparisons of points, team value and remaining cash, with race-by-race snapshots.
- **Chip Strategy** — chip availability and usage across teams, timing of activations and race performance relative to the league average.

Further analysis and visualisation improvements are planned.
