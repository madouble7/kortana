from sqlalchemy import create_engine, inspect


def test_github_tasks_table_has_autonomy_columns():
    """Model metadata should declare the GitHub task autonomy columns."""
    from src.kortana.models import Base

    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("github_tasks")}
    finally:
        engine.dispose()

    assert "classification" in columns
    assert "ho_scaffold" in columns
    assert "code_changes" in columns
    assert "validation_report" in columns
