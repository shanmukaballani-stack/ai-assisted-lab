# Placement Application Tracker

Streamlit tracker for placement applications, using SQLite for storage.

## Run

From the repository root, install the tracker dependencies and start the app:

```powershell
python -m pip install -r PlacementTracker/requirements.txt
python -m streamlit run PlacementTracker/app.py
```

By default, the app creates or reuses `PlacementTracker/placements.db`.
To use an existing database file instead, set `PLACEMENTS_DATABASE_PATH` to
that file's path before starting Streamlit:

```powershell
$env:PLACEMENTS_DATABASE_PATH = "C:\path\to\placements.db"
python -m streamlit run PlacementTracker/app.py
```

The database file is excluded from Git. Existing databases are migrated
automatically to add the optional interview date column without removing
application records.
