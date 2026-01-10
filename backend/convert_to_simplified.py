from app import app, db, Poem
from opencc import OpenCC

def convert_traditional_to_simplified():
    with app.app_context():
        cc = OpenCC('t2s')
        
        poems = Poem.query.all()
        total = len(poems)
        
        print(f'找到 {total} 首诗歌，开始转换...')
        
        for i, poem in enumerate(poems, 1):
            original_title = poem.title
            original_author = poem.author
            original_content = poem.content
            
            poem.title = cc.convert(poem.title)
            poem.author = cc.convert(poem.author)
            poem.content = cc.convert(poem.content)
            
            db.session.commit()
            
            print(f'[{i}/{total}] 已转换: {original_title} -> {poem.title}')
        
        print(f'\n转换完成！共转换 {total} 首诗歌。')

if __name__ == '__main__':
    convert_traditional_to_simplified()
