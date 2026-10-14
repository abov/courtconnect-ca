@echo off
rem Opens courtconnect.duckdb read-only in the DuckDB UI (http://localhost:4213).
rem Close this window (or Ctrl+C) before running dbt build, or the build hits a lock error.
cd /d "%~dp0"
start "" http://localhost:4213
".venv\Scripts\python.exe" -c "import duckdb,time; c=duckdb.connect('courtconnect.duckdb', read_only=True); c.sql('CALL start_ui_server()'); print('DuckDB UI running at http://localhost:4213 - close this window to stop'); time.sleep(10**7)"
