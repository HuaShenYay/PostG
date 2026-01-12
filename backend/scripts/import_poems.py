import json
import os
import sys

# Ensure backend module is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Poem

def import_data(file_path):
    # Resolve absolute path relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)

    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with app.app_context():
        print(f"Importing poems from {file_path}...")
        count = 0
        for item in data:
            title = item.get('title')
            author = item.get('author')
            
            if not title:
                continue

            # Check existing
            existing = Poem.query.filter_by(title=title, author=author).first()
            if existing:
                print(f" - Updating: {title} ({author})")
                existing.content = item.get('content', existing.content)
                existing.dynasty = item.get('dynasty', existing.dynasty)
                existing.translation = item.get('translation', existing.translation)
                existing.appreciation = item.get('appreciation', existing.appreciation)
                existing.author_bio = item.get('author_bio', existing.author_bio)
                if 'notes' in item:
                    existing.notes = json.dumps(item.get('notes'))
            else:
                print(f" - Creating: {title} ({author})")
                new_poem = Poem(
                    title=title,
                    author=author,
                    content=item.get('content'),
                    dynasty=item.get('dynasty', 'Tang'),
                    translation=item.get('translation', ''),
                    appreciation=item.get('appreciation', ''),
                    author_bio=item.get('author_bio', ''),
                    notes=json.dumps(item.get('notes', []))
                )
                db.session.add(new_poem)
            count += 1
        
        db.session.commit()
        print(f"Import complete. Processed {count} poems.")

if __name__ == "__main__":
    import_data('data/poems_sample.json')
