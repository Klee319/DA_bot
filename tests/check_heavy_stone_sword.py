import sqlite3

# データベースに接続
conn = sqlite3.connect('data/items.db')
cursor = conn.cursor()

print("=== ヘビーストーンソードの必要素材確認 ===\n")

# ヘビーストーンソードの必要素材を確認
cursor.execute("SELECT formal_name, required_materials FROM equipments WHERE formal_name LIKE '%ヘビー%' AND required_materials LIKE '%石%'")
for row in cursor.fetchall():
    print(f"装備名: {row[0]}")
    print(f"必要素材: {row[1]}")
    print()

print("=== 石を使用する装備の必要素材フォーマット確認 ===\n")

# 石を使用する装備の必要素材フォーマットを確認
cursor.execute("SELECT formal_name, required_materials FROM equipments WHERE required_materials LIKE '%石%' LIMIT 10")
for row in cursor.fetchall():
    print(f"装備名: {row[0]}")
    print(f"必要素材: {row[1]}")
    print()

conn.close()