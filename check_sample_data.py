import sqlite3

# データベースに接続
conn = sqlite3.connect('data/items.db')
cursor = conn.cursor()

print("=== 関連アイテムテスト用のサンプルデータ ===\n")

# materials
print("【Materials (素材) - 利用先があるもの】")
cursor.execute("""
    SELECT m.formal_name, m.acquisition_category, m.acquisition_method
    FROM materials m
    WHERE EXISTS (
        SELECT 1 FROM equipments e 
        WHERE e.required_materials LIKE '%' || m.formal_name || '%'
    )
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"  - {row[0]} (入手カテゴリ: {row[1]}, 入手方法: {row[2]})")

print("\n【Equipments (装備) - 必要素材があるもの】")
cursor.execute("""
    SELECT formal_name, required_materials, acquisition_category 
    FROM equipments 
    WHERE required_materials IS NOT NULL AND required_materials != ''
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"  - {row[0]}")
    print(f"    必要素材: {row[1]}")
    print(f"    入手カテゴリ: {row[2]}")

print("\n【Mobs (モンスター) - ドロップ品があるもの】")
cursor.execute("""
    SELECT formal_name, drops 
    FROM mobs 
    WHERE drops IS NOT NULL AND drops != ''
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"  - {row[0]}")
    print(f"    ドロップ: {row[1]}")

conn.close()