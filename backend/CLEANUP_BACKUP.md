# 代码审查备份记录

## 创建时间
2024

## Git 备份
在执行任何删除操作前，请确保已创建 Git 备份分支：
```bash
git branch backup-before-cleanup
git checkout backup-before-cleanup
```

## 数据库结构快照

### User 模型 (5个字段)
| 字段名 | 类型 | 使用状态 |
|--------|------|----------|
| id | INTEGER | ✅ 使用中 |
| username | VARCHAR(50) | ✅ 使用中 |
| password_hash | VARCHAR(128) | ✅ 使用中 |
| created_at | DATETIME | ✅ 使用中 |
| preference_topics | TEXT | ✅ 使用中 |

### Poem 模型 (19个字段)
| 字段名 | 类型 | 使用状态 | API位置 |
|--------|------|----------|---------|
| id | INTEGER | ✅ 使用中 | - |
| title | VARCHAR(100) | ✅ 使用中 | 多处 |
| author | VARCHAR(50) | ✅ 使用中 | 多处 |
| content | TEXT | ✅ 使用中 | 多处 |
| dynasty | VARCHAR(20) | ✅ 使用中 | 多处 |
| translation | TEXT | ❌ 未使用 | - |
| appreciation | TEXT | ❌ 未使用 | - |
| author_bio | TEXT | ❌ 未使用 | - |
| notes | TEXT | ❌ 未使用 | - |
| rhythm_name | VARCHAR(50) | ❌ 未使用 | - |
| rhythm_type | VARCHAR(20) | ❌ 未使用 | - |
| tonal_summary | TEXT | ✅ 使用中 | app.py:793 |
| likes | INTEGER | ✅ 使用中 | app.py:946 |
| views | INTEGER | ✅ 使用中 | app.py:947 |
| shares | INTEGER | ✅ 使用中 | app.py:948 |
| tags | TEXT | ❌ 未使用 | - |
| difficulty_level | VARCHAR(10) | ❌ 未使用 | - |
| theme_category | VARCHAR(50) | ❌ 未使用 | - |
| created_at | DATETIME | ✅ 使用中 | 多处 |

### Review 模型 (7个字段)
| 字段名 | 类型 | 使用状态 |
|--------|------|----------|
| id | INTEGER | ✅ 使用中 |
| user_id | INTEGER | ✅ 使用中 |
| poem_id | INTEGER | ✅ 使用中 |
| rating | INTEGER | ✅ 使用中 |
| comment | TEXT | ✅ 使用中 |
| topic_distribution | TEXT | ✅ 使用中 |
| created_at | DATETIME | ✅ 使用中 |

## 待删除文件列表

### 后端脚本 (scripts目录)
- [ ] `analyze_rhythm.py` - 一次性节奏分析脚本
- [ ] `audit_tonal.py` - 声调审计脚本
- [ ] `check_db_status.py` - 数据库状态检查（可保留）
- [ ] `final_check.py` - 最终检查脚本
- [ ] `final_sweep.py` - 最终清理脚本
- [ ] `import_poems.py` - 诗歌导入脚本
- [ ] `populate_metadata.py` - 元数据填充脚本
- [ ] `search_poem.py` - 诗歌搜索脚本
- [ ] `test_recommendations.py` - 推荐测试脚本
- [ ] `verify_api.py` - API验证脚本

### 后端迁移脚本
- [ ] `add_theme_category.py` - 添加主题分类字段
- [ ] `check_data.py` - 数据检查脚本
- [ ] `convert_to_simplified.py` - 简繁体转换
- [ ] `debug_api.py` - API调试脚本
- [ ] `import_data.py` - 数据导入脚本
- [ ] `migrate_db.py` - 数据库迁移
- [ ] `migrate_global_fields.py` - 全局字段迁移
- [ ] `migrate_mysql.py` - MySQL迁移
- [ ] `simple_migrate.py` - 简单迁移
- [ ] `show_lda_results.py` - LDA结果展示

### 批处理文件
- [ ] `add_theme_category.bat`
- [ ] `debug_api.bat`
- [ ] `fix_api_errors.bat`
- [ ] `run_migrate.bat`
- [ ] `start_server.bat`
- [ ] `test_api.bat`
- [ ] `test_integration.bat`

### 前端组件
- [ ] `components/HelloWorld.vue` - 未被使用的示例组件

## 备份验证
在执行删除前，请验证：
1. [ ] Git 备份分支已创建
2. [ ] 数据库已导出结构快照
3. [ ] 测试环境可运行
