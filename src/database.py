import sqlite3
import aiosqlite
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "./data/items.db"):
        self.db_path = db_path
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        """データベースファイルのディレクトリが存在することを確認"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def initialize_database(self):
        """データベースを初期化し、全テーブルを作成"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await self._create_indexes(db)
            await db.commit()
        logger.info("データベースの初期化が完了しました")
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """全テーブルを作成"""
        
        # equipments テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS equipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formal_name TEXT NOT NULL UNIQUE,
                common_name TEXT,
                acquisition_location TEXT,
                acquisition_category TEXT,
                type TEXT,
                required_materials TEXT,
                item_effect TEXT,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # materials テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formal_name TEXT NOT NULL UNIQUE,
                common_name TEXT,
                acquisition_category TEXT,
                acquisition_method TEXT,
                usage_category TEXT,
                usage_purpose TEXT,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # mobs テーブル（同名正式名称でも必要レベル違いは別モブとして扱う）
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formal_name TEXT NOT NULL,
                common_name TEXT,
                area TEXT,
                area_detail TEXT,
                required_level TEXT,
                drops TEXT,
                exp TEXT,
                gold TEXT,
                required_defense INTEGER,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(formal_name, required_level)
            )
        ''')
        
        # gatherings テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS gatherings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                collection_method TEXT,
                obtained_materials TEXT,
                required_tools TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 既存のgatheringsテーブルにusageカラムが存在する場合は再構築
        await self._migrate_gatherings_table(db)
        
        # user_favorites テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, item_name, item_type)
            )
        ''')
        
        # search_history テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                result_count INTEGER,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # search_stats テーブル
        await db.execute('''
            CREATE TABLE IF NOT EXISTS search_stats (
                item_name TEXT PRIMARY KEY,
                search_count INTEGER DEFAULT 1,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    async def _create_indexes(self, db: aiosqlite.Connection):
        """パフォーマンス向上のためのインデックスを作成"""
        indexes = [
            # 検索性能向上のためのインデックス
            "CREATE INDEX IF NOT EXISTS idx_equipments_formal_name ON equipments(formal_name)",
            "CREATE INDEX IF NOT EXISTS idx_equipments_common_name ON equipments(common_name)",
            "CREATE INDEX IF NOT EXISTS idx_materials_formal_name ON materials(formal_name)",
            "CREATE INDEX IF NOT EXISTS idx_materials_common_name ON materials(common_name)",
            "CREATE INDEX IF NOT EXISTS idx_mobs_formal_name ON mobs(formal_name)",
            "CREATE INDEX IF NOT EXISTS idx_mobs_common_name ON mobs(common_name)",
            
            # 履歴とお気に入りのインデックス
            "CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_searched_at ON search_history(searched_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id)",
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    async def search_items(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """アイテムを検索（全テーブル対象）"""
        results = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 各テーブルから検索
            tables = ['equipments', 'materials', 'mobs']
            
            for table in tables:
                # 正式名称での完全一致検索
                cursor = await db.execute(
                    f"SELECT *, '{table}' as item_type FROM {table} WHERE formal_name = ? LIMIT ?",
                    (query, limit)
                )
                rows = await cursor.fetchall()
                results.extend([dict(row) for row in rows])
                
                # 一般名称での完全一致検索（まだ見つからない場合）
                if not results:
                    cursor = await db.execute(
                        f"SELECT *, '{table}' as item_type FROM {table} WHERE common_name = ? LIMIT ?",
                        (query, limit)
                    )
                    rows = await cursor.fetchall()
                    results.extend([dict(row) for row in rows])
        
        return results[:limit]
    
    async def add_search_history(self, user_id: str, query: str, result_count: int):
        """検索履歴を追加"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO search_history (user_id, query, result_count) VALUES (?, ?, ?)",
                (user_id, query, result_count)
            )
            await db.commit()
    
    async def update_search_stats(self, item_name: str):
        """検索統計を更新"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO search_stats (item_name, search_count, last_searched)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(item_name) DO UPDATE SET
                    search_count = search_count + 1,
                    last_searched = CURRENT_TIMESTAMP
            ''', (item_name,))
            await db.commit()
    
    async def add_favorite(self, user_id: str, item_name: str, item_type: str) -> bool:
        """お気に入りアイテムを追加"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO user_favorites (user_id, item_name, item_type) VALUES (?, ?, ?)",
                    (user_id, item_name, item_type)
                )
                await db.commit()
                return True
        except sqlite3.IntegrityError:
            # 既に存在する場合
            return False
    
    async def remove_favorite(self, user_id: str, item_name: str, item_type: str) -> bool:
        """お気に入りアイテムを削除"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM user_favorites WHERE user_id = ? AND item_name = ? AND item_type = ?",
                (user_id, item_name, item_type)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """ユーザーのお気に入りアイテム一覧を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_favorites WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_search_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """ユーザーの検索履歴を取得"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM search_history WHERE user_id = ? AND searched_at > ? ORDER BY searched_at DESC LIMIT 50",
                (user_id, cutoff_date)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_search_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """検索ランキングを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM search_stats ORDER BY search_count DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def clear_old_search_history(self, days: int = 30):
        """古い検索履歴をクリア"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM search_history WHERE searched_at < ?",
                (cutoff_date,)
            )
            await db.commit()
    
    async def backup_database(self, backup_path: str):
        """データベースをバックアップ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/backup_{timestamp}.db"
        
        # バックアップディレクトリを作成
        os.makedirs(backup_path, exist_ok=True)
        
        # ファイルをコピー
        async with aiosqlite.connect(self.db_path) as source:
            async with aiosqlite.connect(backup_file) as dest:
                await source.backup(dest)
        
        logger.info(f"データベースをバックアップしました: {backup_file}")
        return backup_file
    
    async def _migrate_gatherings_table(self, db: aiosqlite.Connection):
        """gatheringsテーブルからusageカラムを削除するマイグレーション"""
        try:
            # テーブル構造を確認
            cursor = await db.execute("PRAGMA table_info(gatherings)")
            columns = await cursor.fetchall()
            
            # usageカラムが存在するかチェック
            has_usage = any(col[1] == 'usage' for col in columns)
            
            if has_usage:
                logger.info("gatheringsテーブルからusageカラムを削除します")
                
                # 既存データをバックアップ
                await db.execute('''
                    CREATE TEMPORARY TABLE gatherings_backup AS 
                    SELECT id, location, collection_method, obtained_materials, 
                           required_tools, description, created_at, updated_at
                    FROM gatherings
                ''')
                
                # 既存テーブルを削除
                await db.execute('DROP TABLE gatherings')
                
                # 新しいテーブルを作成
                await db.execute('''
                    CREATE TABLE gatherings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        location TEXT NOT NULL,
                        collection_method TEXT,
                        obtained_materials TEXT,
                        required_tools TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # データを復元
                await db.execute('''
                    INSERT INTO gatherings 
                    SELECT * FROM gatherings_backup
                ''')
                
                # 一時テーブルを削除
                await db.execute('DROP TABLE gatherings_backup')
                
                logger.info("gatheringsテーブルのマイグレーションが完了しました")
                
        except Exception as e:
            logger.warning(f"gatheringsテーブルのマイグレーション中にエラー: {e}")