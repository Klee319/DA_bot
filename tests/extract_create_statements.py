#!/usr/bin/env python3
"""データベースのCREATE TABLE文を抽出するスクリプト"""
import sqlite3
import os

db_path = "./data/items.db"

if not os.path.exists(db_path):
    print(f"データベースファイルが見つかりません: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# CREATE TABLE文を取得
cursor.execute("""
    SELECT sql 
    FROM sqlite_master 
    WHERE type='table' 
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""")

results = cursor.fetchall()

print("=== CREATE TABLE文一覧 ===")
for i, (sql,) in enumerate(results):
    if sql:  # sqlがNoneでない場合のみ表示
        print(f"\n-- {i+1}. テーブル定義 --")
        print(sql)

# インデックスのCREATE文も取得
cursor.execute("""
    SELECT sql 
    FROM sqlite_master 
    WHERE type='index' 
    AND sql IS NOT NULL
    ORDER BY name
""")

index_results = cursor.fetchall()

if index_results:
    print("\n\n=== CREATE INDEX文一覧 ===")
    for i, (sql,) in enumerate(index_results):
        if sql:
            print(f"\n-- {i+1}. インデックス定義 --")
            print(sql)

conn.close()