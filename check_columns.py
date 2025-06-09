import sqlite3

# データベースに接続
conn = sqlite3.connect('data/items.db')
cursor = conn.cursor()

print("=== テーブル構造の確認 ===\n")

# materials テーブルの構造
print("【Materials テーブル】")
cursor.execute("PRAGMA table_info(materials)")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")

print("\n【Equipments テーブル】")
cursor.execute("PRAGMA table_info(equipments)")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")

print("\n【Mobs テーブル】")
cursor.execute("PRAGMA table_info(mobs)")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")

conn.close()