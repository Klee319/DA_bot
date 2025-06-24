#!/usr/bin/env python3
"""ワイルドカードアイテムの確認"""

import asyncio
import aiosqlite

async def check_wildcard_items():
    """データベース内のワイルドカードアイテムを確認"""
    async with aiosqlite.connect('./data/items.db') as db:
        db.row_factory = aiosqlite.Row
        
        # 各テーブルのワイルドカードアイテムを検索
        tables = ['materials', 'equipments', 'mobs']
        
        for table in tables:
            print(f"\n=== {table}テーブル ===")
            
            # ワイルドカードを含むアイテムを検索
            cursor = await db.execute(
                f"SELECT formal_name, description FROM {table} WHERE formal_name LIKE '%*%' OR formal_name LIKE '%＊%' OR formal_name LIKE '%?%' OR formal_name LIKE '%？%' LIMIT 10"
            )
            rows = await cursor.fetchall()
            
            if rows:
                for row in rows:
                    desc = row['description'] if row['description'] else 'なし'
                    if len(desc) > 50:
                        desc = desc[:50] + '...'
                    print(f"  {row['formal_name']} - 説明: {desc}")
            else:
                print("  ワイルドカードアイテムが見つかりません")
        
        # 特定のアイテムの検索
        print("\n=== 特定アイテムの検索 ===")
        test_names = ['魔法石', 'エフォート・エビデンス', '重厚な石剣']
        
        for name in test_names:
            print(f"\n'{name}'を含むアイテム:")
            for table in tables:
                cursor = await db.execute(
                    f"SELECT formal_name, description FROM {table} WHERE formal_name LIKE ? LIMIT 3",
                    (f'%{name}%',)
                )
                rows = await cursor.fetchall()
                
                for row in rows:
                    desc = row['description'] if row['description'] else 'なし'
                    if len(desc) > 30:
                        desc = desc[:30] + '...'
                    print(f"  [{table}] {row['formal_name']} - 説明: {desc}")

if __name__ == "__main__":
    asyncio.run(check_wildcard_items())