from models import db, Poem
from app import app
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_import():
    """验证诗歌数据导入的完整性和准确性"""
    with app.app_context():
        # 1. 检查总数量
        total_poems = Poem.query.count()
        logger.info(f"数据库中共有 {total_poems} 首诗歌")
        
        # 2. 检查必填字段是否完整
        incomplete_poems = Poem.query.filter(
            (Poem.title == '') | 
            (Poem.content == '') | 
            (Poem.author == '')
        ).all()
        
        if incomplete_poems:
            logger.error(f"发现 {len(incomplete_poems)} 首诗歌缺少必填字段")
            for poem in incomplete_poems[:10]:  # 只显示前10个
                logger.error(f"  - ID: {poem.id}, 标题: {poem.title}, 作者: {poem.author}")
        else:
            logger.info("所有诗歌必填字段完整")
        
        # 3. 检查朝代分布
        from sqlalchemy import func
        dynasty_stats = db.session.query(
            Poem.dynasty,
            func.count(Poem.id)
        ).group_by(Poem.dynasty).all()
        
        logger.info("诗歌朝代分布:")
        for dynasty, count in dynasty_stats:
            logger.info(f"  - {dynasty}: {count} 首")
        
        # 4. 检查诗歌类型分布
        genre_stats = db.session.query(
            Poem.genre_type,
            func.count(Poem.id)
        ).group_by(Poem.genre_type).all()
        
        logger.info("诗歌类型分布:")
        for genre, count in genre_stats:
            logger.info(f"  - {genre}: {count} 首")
        
        # 5. 随机抽查几首诗歌内容
        logger.info("随机抽查5首诗歌内容:")
        import random
        poems = Poem.query.all()
        if poems:
            sampled_poems = random.sample(poems, min(5, len(poems)))
            for poem in sampled_poems:
                logger.info(f"\n  ID: {poem.id}")
                logger.info(f"  标题: {poem.title}")
                logger.info(f"  作者: {poem.author}")
                logger.info(f"  朝代: {poem.dynasty}")
                logger.info(f"  类型: {poem.genre_type}")
                logger.info(f"  格律: {poem.rhythm_type}")
                logger.info(f"  内容: {poem.content[:100]}...")
        
        # 6. 检查是否有重复标题和作者的诗歌
        from sqlalchemy import distinct
        unique_poems = db.session.query(
            Poem.title,
            Poem.author,
            func.count(Poem.id)
        ).group_by(Poem.title, Poem.author).having(func.count(Poem.id) > 1).all()
        
        if unique_poems:
            logger.warning(f"发现 {len(unique_poems)} 组重复的诗歌(标题和作者相同):")
            for title, author, count in unique_poems:
                logger.warning(f"  - {title} ({author}): {count} 首")
        else:
            logger.info("未发现重复的诗歌")
        
        # 7. 验证结果总结
        logger.info("\n" + "="*50)
        logger.info("验证结果总结")
        logger.info("="*50)
        
        if total_poems >= 360:  # 预期366首
            logger.info("✅ 数据量验证通过")
        else:
            logger.error("❌ 数据量验证失败")
        
        if len(incomplete_poems) == 0:
            logger.info("✅ 必填字段验证通过")
        else:
            logger.error("❌ 必填字段验证失败")
        
        # 检查是否所有诗歌都有朝代
        no_dynasty = Poem.query.filter(Poem.dynasty == '').count()
        if no_dynasty == 0:
            logger.info("✅ 朝代信息验证通过")
        else:
            logger.error(f"❌ 有 {no_dynasty} 首诗歌缺少朝代信息")
        
        logger.info("验证完成！")

if __name__ == '__main__':
    verify_import()
