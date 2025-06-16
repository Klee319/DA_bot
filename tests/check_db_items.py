import sqlite3

# データベースに接続
conn = sqlite3.connect('data/items.db')
cursor = conn.cursor()

print("=== データベース内のアイテム ===\n")

# materials
print("【Materials (素材)】")
cursor.execute("SELECT formal_name, acquisition_category, acquisition_source FROM materials LIMIT 5")
for row in cursor.fetchall():
    print(f"  - {row[0]} (入手: {row[1]}, ソース: {row[2]})")

print("\n【Equipments (装備)】")
cursor.execute("SELECT formal_name, required_materials, acquisition_category FROM equipments LIMIT 5")
for row in cursor.fetchall():
    print(f"  - {row[0]} (必要素材: {row[1]}, 入手: {row[2]})")

print("\n【Mobs (モンスター)】")
cursor.execute("SELECT formal_name, drops FROM mobs LIMIT 5")
for row in cursor.fetchall():
    print(f"  - {row[0]} (ドロップ: {row[1]})")

conn.close()