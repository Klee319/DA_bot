#!/usr/bin/env python3
"""
データベース内容の確認
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager
import aiosqlite

async def check_db_contents():
    """データベース内容の確認"""
    print("📝 データベース内容確認開始...")
    
    db_manager = DatabaseManager()
    
    try:
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            tables = ['equipments', 'materials', 'mobs']
            
            for table in tables:
                print(f"\n📋 {table}テーブル:")
                cursor = await db.execute(f"SELECT formal_name, common_name FROM {table} LIMIT 10")
                rows = await cursor.fetchall()
                
                for i, row in enumerate(rows, 1):
                    formal_name = row[0] or "None"
                    common_name = row[1] or "None"
                    print(f"  {i}. {formal_name} ({common_name})")
                
                # 総件数も表示
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = await cursor.fetchone()
                print(f"  総件数: {count[0]}件")
                
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print("\n✅ データベース内容確認完了!")

if __name__ == "__main__":
    asyncio.run(check_db_contents())