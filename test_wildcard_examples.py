#!/usr/bin/env python3
"""
ワイルドカード検索の使用例
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.search_engine import SearchEngine
from src.database import DatabaseManager

async def show_wildcard_examples():
    """ワイルドカード検索の使用例を表示"""
    print("📝 ワイルドカード検索の使用例")
    print("=" * 50)
    
    # 設定
    config = {
        'features': {
            'pagination_size': 5  # 例なので5件に制限
        }
    }
    
    db_manager = DatabaseManager()
    search_engine = SearchEngine(db_manager, config)
    
    examples = [
        {
            "query": "*ソード*",
            "description": "「ソード」を含む全てのアイテムを検索",
            "pattern": "前後任意文字 + 特定文字列 + 前後任意文字"
        },
        {
            "query": "ウッド*",
            "description": "「ウッド」で始まるアイテムを検索",
            "pattern": "特定文字列 + 後続任意文字"
        },
        {
            "query": "*スライム",
            "description": "「スライム」で終わるアイテムを検索",
            "pattern": "前方任意文字 + 特定文字列"
        },
        {
            "query": "?ト",
            "description": "2文字目が「ト」のアイテムを検索",
            "pattern": "任意1文字 + 特定文字"
        },
        {
            "query": "???",
            "description": "3文字のアイテムを検索",
            "pattern": "任意1文字 × 3"
        }
    ]
    
    for example in examples:
        query = example["query"]
        description = example["description"]
        pattern = example["pattern"]
        
        print(f"\n🔍 検索パターン: {pattern}")
        print(f"📝 説明: {description}")
        print(f"💬 クエリ: '{query}'")
        
        results = await search_engine.search(query)
        
        if results:
            print(f"✅ {len(results)}件の結果:")
            for i, result in enumerate(results, 1):
                formal_name = result.get('formal_name', 'Unknown')
                item_type = result.get('item_type', 'unknown')
                common_name = result.get('common_name', '')
                display_name = f"{formal_name}"
                if common_name:
                    display_name += f" ({common_name})"
                print(f"  {i}. {display_name} [{item_type}]")
        else:
            print("❌ 結果なし")
        
        print("-" * 40)
    
    print("\n📋 ワイルドカード文字の説明:")
    print("  * (アスタリスク) : 0文字以上の任意の文字列")
    print("  ? (クエスチョン): 任意の1文字")
    print("  全角文字（＊、？）も使用可能")
    print("\n✅ ワイルドカード検索の使用例完了!")

if __name__ == "__main__":
    asyncio.run(show_wildcard_examples())