import sys
sys.path.insert(0, '/app')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:////var/www/mycourse/db/mycourse.db')
Session = sessionmaker(bind=engine)

def migrate():
    with Session() as session:
        try:
            session.execute(text('ALTER TABLE term ADD COLUMN is_active BOOLEAN DEFAULT 0'))
            session.commit()
            print('Added is_active column to term')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print('is_active column already exists in term')
            else:
                raise

        try:
            session.execute(text('ALTER TABLE score_record ADD COLUMN term_id INTEGER REFERENCES term(id)'))
            session.commit()
            print('Added term_id column to score_record')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print('term_id column already exists in score_record')
            else:
                raise

        # Set first term as active
        result = session.execute(text('SELECT id FROM term LIMIT 1')).fetchone()
        if result:
            first_term_id = result[0]
            session.execute(text('UPDATE term SET is_active = 1 WHERE id = :id'), {'id': first_term_id})
            session.commit()
            print(f'Set term {first_term_id} as active')

            # Update all score records to point to this term
            session.execute(text('UPDATE score_record SET term_id = :term_id WHERE term_id IS NULL'), {'term_id': first_term_id})
            session.commit()
            print('Updated score records')
        else:
            print('No terms found')

if __name__ == '__main__':
    migrate()
