import sys
sys.path.insert(0, '/app')
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:////var/www/mycourse/db/mycourse.db')

with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print('Tables:', result)

    result = conn.execute(text("SELECT COUNT(*) FROM term")).fetchone()
    print('Term count:', result[0])

    result = conn.execute(text("SELECT COUNT(*) FROM score_record")).fetchone()
    print('Score record count:', result[0])
