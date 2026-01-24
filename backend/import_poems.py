import json
import os
from datetime import datetime
from models import db, Poem
from app import app

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clean_text(text):
    """清洗文本，处理特殊字符"""
    if not text:
        return text
    # 移除可能的BOM头
    if text.startswith('\ufeff'):
        text = text[1:]
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 移除多余的空格
    text = ' '.join(text.split())
    return text

def get_poem_type_from_tags(tags):
    """从标签中提取诗歌类型"""
    poem_types = {
        '五言绝句': '诗',
        '七言绝句': '诗',
        '五言律诗': '诗',
        '七言律诗': '诗',
        '五言古诗': '诗',
        '七言古诗': '诗',
        '乐府': '诗',
        '新乐府辞': '诗',
        '鼓吹曲辞': '诗',
        '横吹曲辞': '诗'
    }
    for tag in tags:
        if tag in poem_types:
            return poem_types[tag]
    return '诗'  # 默认值

def get_rhythm_type_from_tags(tags):
    """从标签中提取格律类型"""
    rhythm_types = {
        '五言绝句': '绝句',
        '七言绝句': '绝句',
        '五言律诗': '律诗',
        '七言律诗': '律诗',
        '五言古诗': '古诗',
        '七言古诗': '古诗'
    }
    for tag in tags:
        if tag in rhythm_types:
            return rhythm_types[tag]
    return None

def import_poems():
    """导入唐诗三百首数据"""
    # 读取JSON文件
    json_file_path = r'c:\PostG\data\chinese-poetry\全唐诗\唐诗三百首.json'
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            poems_data = json.load(f)
        logger.info(f"成功读取JSON文件，共包含 {len(poems_data)} 首诗歌")
    except Exception as e:
        logger.error(f"读取JSON文件失败: {str(e)}")
        return False
    
    success_count = 0
    failure_count = 0
    failure_reasons = []
    
    # 使用Flask应用上下文
    with app.app_context():
        for i, poem_item in enumerate(poems_data, 1):
            try:
                # 数据清洗和映射
                title = clean_text(poem_item.get('title', ''))
                author = clean_text(poem_item.get('author', ''))
                
                # 处理段落，合并为单字符串
                paragraphs = poem_item.get('paragraphs', [])
                content = '\n'.join([clean_text(para) for para in paragraphs])
                
                # 朝代默认为唐
                dynasty = '唐'
                
                # 从标签提取诗歌类型和格律信息
                tags = poem_item.get('tags', [])
                genre_type = get_poem_type_from_tags(tags)
                rhythm_type = get_rhythm_type_from_tags(tags)
                
                # 检查必填字段
                if not title:
                    raise ValueError("缺少标题")
                if not content:
                    raise ValueError("缺少内容")
                
                # 创建Poem对象
                poem = Poem(
                    title=title,
                    author=author,
                    content=content,
                    dynasty=dynasty,
                    genre_type=genre_type,
                    rhythm_name=poem_item.get('title', ''),  # 暂时使用标题作为格律名
                    rhythm_type=rhythm_type,
                    views=0,
                    review_count=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # 添加到数据库
                db.session.add(poem)
                
                # 每10首诗提交一次
                if i % 10 == 0:
                    db.session.commit()
                    logger.info(f"已提交 {i} 首诗歌")
                
                success_count += 1
            
            except Exception as e:
                failure_count += 1
                failure_reasons.append(f"第 {i} 首诗导入失败: {str(e)}")
                logger.error(f"第 {i} 首诗导入失败: {str(e)}")
                continue
        
        # 提交剩余的诗歌
        db.session.commit()
        logger.info("所有诗歌已提交到数据库")
    
    # 生成导入报告
    logger.info("=" * 50)
    logger.info("导入报告")
    logger.info("=" * 50)
    logger.info(f"总条目数: {len(poems_data)}")
    logger.info(f"成功导入: {success_count}")
    logger.info(f"导入失败: {failure_count}")
    
    if failure_reasons:
        logger.info("失败原因:")
        for reason in failure_reasons:
            logger.info(f"  - {reason}")
    
    logger.info("导入完成！")
    return True

if __name__ == '__main__':
    import_poems()
