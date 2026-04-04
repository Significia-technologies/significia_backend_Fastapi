import os
import glob
from sqlalchemy import create_engine, text

# Configuration
DATABASE_URL = "postgresql+psycopg://significia:significia@localhost:5432/significia"
VERSIONS_PATH = os.path.join("alembic", "versions", "*.py")

def reset_alembic():
    # 1. Delete migration files
    print(f"Deleting migration files in {VERSIONS_PATH}...")
    files = glob.glob(VERSIONS_PATH)
    for f in files:
        if "__init__.py" not in f:
            os.remove(f)
            print(f"Deleted: {f}")

    # 2. Drop alembic_version table
    print("Dropping alembic_version table in the database...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            conn.commit()
            print("Successfully dropped alembic_version table.")
    except Exception as e:
        print(f"Error dropping table: {e}")

if __name__ == "__main__":
    reset_alembic()
