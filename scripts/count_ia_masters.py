from app.database.session import SessionLocal
from app.models.ia_master import IAMaster
import sys

def count_ia_masters():
    db = SessionLocal()
    try:
        count = db.query(IAMaster).count()
        print(f"Total IA Masters in core DB: {count}")
    except Exception as e:
        print(f"Error checking core DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    count_ia_masters()
