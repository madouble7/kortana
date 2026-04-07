from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_github_tasks_table_has_autonomy_columns(test_db_url, setup_test_db):
    """Alembic migrations should create the GitHub task fields used by the model."""
    backend_dir = Path(__file__).resolve().parents[1]
    relative_db_path = test_db_url.replace("sqlite+aiosqlite:///", "")
    db_path = (backend_dir / relative_db_path).resolve()
    sync_url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(sync_url)
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("github_tasks")}
    finally:
        engine.dispose()

    assert "classification" in columns
    assert "ho_scaffold" in columns
    assert "code_changes" in columns
    assert "validation_report" in columns
