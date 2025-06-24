#!/usr/bin/env python3
"""データベーススキーマを確認するスクリプト"""
import sqlite3
import os

db_path = "./data/items.db"

if not os.path.exists(db_path):
    print(f"データベースファイルが見つかりません: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=== データベーステーブル一覧 ===")
for table in tables:
    print(f"\n■ {table[0]}")
    
    # テーブル構造を取得
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    
    print("カラム構造:")
    for col in columns:
        cid, name, type_, notnull, dflt_value, pk = col
        pk_str = " PRIMARY KEY" if pk else ""
        notnull_str = " NOT NULL" if notnull else ""
        default_str = f" DEFAULT {dflt_value}" if dflt_value else ""
        print(f"  - {name}: {type_}{pk_str}{notnull_str}{default_str}")
    
    # インデックスを取得
    cursor.execute(f"PRAGMA index_list({table[0]})")
    indexes = cursor.fetchall()
    
    if indexes:
        print("\nインデックス:")
        for idx in indexes:
            print(f"  - {idx[1]}")

conn.close()