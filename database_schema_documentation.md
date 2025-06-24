# データベーススキーマ定義書

## 概要
このドキュメントでは、Discord Bot用のSQLiteデータベース（`data/items.db`）のテーブル構造を定義しています。

## テーブル一覧

### 1. equipments（装備品テーブル）
装備品アイテムの情報を管理するテーブル

```sql
CREATE TABLE equipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL UNIQUE,      -- 正式名称（ユニーク制約）
    common_name TEXT,                       -- 一般名称
    acquisition_location TEXT,              -- 入手場所
    acquisition_category TEXT,              -- 入手カテゴリ
    type TEXT,                              -- 装備タイプ
    required_materials TEXT,                -- 必要素材（JSON形式）
    item_effect TEXT,                       -- アイテム効果
    description TEXT,                       -- 説明文
    image_url TEXT,                         -- 画像URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 2. materials（素材テーブル）
素材アイテムの情報を管理するテーブル

```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL UNIQUE,      -- 正式名称（ユニーク制約）
    common_name TEXT,                       -- 一般名称
    acquisition_category TEXT,              -- 入手カテゴリ
    acquisition_method TEXT,                -- 入手方法
    usage_category TEXT,                    -- 使用カテゴリ
    usage_purpose TEXT,                     -- 使用目的
    description TEXT,                       -- 説明文
    image_url TEXT,                         -- 画像URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 3. mobs（モブテーブル）
モンスター情報を管理するテーブル（同名でも必要レベルが異なれば別エントリ）

```sql
CREATE TABLE mobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL,              -- 正式名称
    common_name TEXT,                       -- 一般名称
    area TEXT,                              -- エリア
    area_detail TEXT,                       -- エリア詳細
    required_level TEXT,                    -- 必要レベル
    drops TEXT,                             -- ドロップアイテム（JSON形式）
    exp TEXT,                               -- 経験値
    gold TEXT,                              -- ゴールド
    required_defense INTEGER,               -- 必要防御力
    description TEXT,                       -- 説明文
    image_url TEXT,                         -- 画像URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(formal_name, required_level)     -- 複合ユニーク制約
)
```

### 4. gatherings（採集テーブル）
採集場所の情報を管理するテーブル

```sql
CREATE TABLE gatherings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,                 -- 採集場所
    collection_method TEXT,                 -- 採集方法
    obtained_materials TEXT,                -- 入手可能素材（JSON形式）
    required_tools TEXT,                    -- 必要道具
    description TEXT,                       -- 説明文
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 5. npcs（NPCテーブル）
NPC情報を管理するテーブル

```sql
CREATE TABLE npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,                 -- NPC所在地
    name TEXT NOT NULL,                     -- NPC名
    business_type TEXT,                     -- 営業タイプ
    obtainable_items TEXT,                  -- 入手可能アイテム（JSON形式）
    required_materials TEXT,                -- 必要素材（JSON形式）
    exp TEXT,                               -- 経験値
    gold TEXT,                              -- ゴールド
    description TEXT,                       -- 説明文
    image_path TEXT,                        -- 画像パス
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(location, name, business_type)   -- 複合ユニーク制約
)
```

### 6. user_favorites（お気に入りテーブル）
ユーザーのお気に入りアイテムを管理するテーブル

```sql
CREATE TABLE user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- DiscordユーザーID
    item_name TEXT NOT NULL,                -- アイテム名
    item_type TEXT NOT NULL,                -- アイテムタイプ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, item_name, item_type)   -- 複合ユニーク制約
)
```

### 7. search_history（検索履歴テーブル）
ユーザーの検索履歴を管理するテーブル

```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- DiscordユーザーID
    query TEXT NOT NULL,                    -- 検索クエリ
    result_count INTEGER,                   -- 検索結果数
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 8. search_stats（検索統計テーブル）
アイテムの検索統計を管理するテーブル

```sql
CREATE TABLE search_stats (
    item_name TEXT PRIMARY KEY,             -- アイテム名（主キー）
    search_count INTEGER DEFAULT 1,         -- 検索回数
    last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## インデックス一覧

パフォーマンス向上のため、以下のインデックスが作成されています：

```sql
-- equipmentsテーブル
CREATE INDEX idx_equipments_formal_name ON equipments(formal_name);
CREATE INDEX idx_equipments_common_name ON equipments(common_name);

-- materialsテーブル
CREATE INDEX idx_materials_formal_name ON materials(formal_name);
CREATE INDEX idx_materials_common_name ON materials(common_name);

-- mobsテーブル
CREATE INDEX idx_mobs_formal_name ON mobs(formal_name);
CREATE INDEX idx_mobs_common_name ON mobs(common_name);

-- user_favoritesテーブル
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);

-- search_historyテーブル
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_searched_at ON search_history(searched_at);
```

## データ形式の詳細

### JSON形式のフィールド
以下のフィールドはJSON形式でデータを格納します：

- `equipments.required_materials`: 必要素材のリスト
- `mobs.drops`: ドロップアイテムのリスト
- `gatherings.obtained_materials`: 入手可能素材のリスト
- `npcs.obtainable_items`: 入手可能アイテムのリスト
- `npcs.required_materials`: 必要素材のリスト

### タイムスタンプ
- `created_at`: レコード作成時刻（自動設定）
- `updated_at`: レコード更新時刻（自動設定）
- `searched_at`: 検索実行時刻（自動設定）
- `last_searched`: 最終検索時刻（自動設定）

## 注意事項

1. **ユニーク制約**
   - `equipments`と`materials`の`formal_name`はユニーク
   - `mobs`は`formal_name`と`required_level`の組み合わせでユニーク
   - `npcs`は`location`、`name`、`business_type`の組み合わせでユニーク
   - `user_favorites`は`user_id`、`item_name`、`item_type`の組み合わせでユニーク

2. **データ型**
   - IDフィールドは全て`INTEGER PRIMARY KEY AUTOINCREMENT`
   - テキストフィールドは基本的に`TEXT`型
   - 数値フィールドは`INTEGER`型（`required_defense`のみ）

3. **NULL制約**
   - 重要なフィールドには`NOT NULL`制約が設定されています
   - 特に各テーブルの主要な識別フィールド（`formal_name`、`location`、`name`など）

## 関連ファイル

- **データベース管理クラス**: `/app/product/DA_discord/src/database.py`
- **データベースファイル**: `/app/product/DA_discord/data/items.db`
- **未実装テーブル仕様**: `/app/product/DA_discord/ref/table_specifications_todo.md`