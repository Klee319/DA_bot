# Discord DA アイテム参照BOT仕様書 v2.0

最終更新: 2025-06-24

## 1. 概要

Discord上で動作するアイテム情報検索BOT。装備・素材・モブ・NPC・採集情報を統合的に検索・表示する。

## 2. 機能仕様

### 2.1 基本検索機能

#### コマンド形式
```
!da <検索キーワード>
```

#### 検索対象
- 装備品（equipments）
- 素材（materials）
- モンスター（mobs）
- NPC（npcs）
- 採集場所（gatherings）

#### 検索方式
1. **完全一致検索**（正式名称・一般名称）
2. **レベル/ランク除去検索**
   - Lv〇〇、レベル〇〇、ランク〇〇、★〇〇を自動除去
3. **ワイルドカード検索**
   - 前方一致：`*破片`（○○破片にマッチ）
   - 後方一致：`グロースクリスタル*`（グロースクリスタル○○にマッチ）
   - 中間一致：`【圧縮】*`（【圧縮】○○にマッチ）
4. **表記ゆれ対応**
   - ひらがな⇔カタカナ⇔漢字の相互変換
   - 全角⇔半角の自動変換
5. **部分一致検索**（最終手段）

### 2.2 表示機能

#### Embed表示
- タイトル：アイテム名（ワイルドカードの場合は検索クエリ）
- カラー：アイテムタイプ別（装備:青、素材:緑、モブ:赤、採集:橙、NPC:紫）
- フィールド：アイテムタイプ別の詳細情報
- サムネイル：アイテム画像（有効なURLの場合）

#### インタラクティブ要素
1. **プルダウンメニュー**
   - 複数検索結果からの選択
   - ドロップアイテム詳細（モブ）
   - 必要素材詳細（装備）
   - 交換内容詳細（NPC）

2. **ボタン**
   - 入手元詳細（素材・装備）
   - 利用先詳細（素材）
   - ※ワイルドカードアイテムは非表示

### 2.3 管理機能

#### 権限管理
- 管理者ロール：`Bot管理者`
- 管理者ユーザー：config.jsonで個別指定
- チャンネル制限：allowed_channelsで使用可能チャンネル指定

#### 管理コマンド
- `!da-update`：CSVファイルからデータベース更新
- `!da-backup`：データベースバックアップ
- `!da-reload`：設定ファイル再読み込み

### 2.4 特殊機能

#### ワイルドカードアイテム対応
- `*破片`のようなワイルドカードアイテムを正しく表示
- モブのドロップにワイルドカードアイテムも含める
- ワイルドカードアイテムの説明文を類似アイテムから取得

#### 個数表示の統一
- すべての個数表示を`×`（かける）で統一
- 例：`木の棒×8`

## 3. データベース構造

### 実装済みテーブル

#### equipments（装備品）
- id, formal_name, common_name
- acquisition_category, acquisition_location, type
- required_materials, required_level, item_effect
- description, image_url
- created_at, updated_at

#### materials（素材）
- id, formal_name, common_name
- acquisition_category, acquisition_method
- usage_category, usage_purpose
- description, image_url
- created_at, updated_at

#### mobs（モンスター）
- id, formal_name, common_name
- area, area_detail, required_level
- drops, exp, gold, required_defense
- description, image_url
- created_at, updated_at

#### npcs（NPC）
- id, location, name, business_type
- obtainable_items, required_materials
- exp, gold, description, image_url
- created_at, updated_at

#### gatherings（採集場所）
- id, location, collection_method
- resource_name, obtained_materials
- required_tools, description, image_url
- created_at, updated_at

#### user_favorites（お気に入り）※未実装
- id, user_id, item_name, item_type, created_at

#### search_history（検索履歴）※未実装
- id, user_id, query, result_count, searched_at

#### search_stats（検索統計）※未実装
- item_name, search_count, last_searched

### 未実装テーブル

#### gathering_locations（詳細採集場所）
- より詳細な採集情報（座標、成功率、リスポーン時間等）

## 4. 設定ファイル

### config.json
```json
{
    "bot": {
        "token": "DISCORD_BOT_TOKEN",
        "prefix": "!",
        "owner_id": "OWNER_DISCORD_ID"
    },
    "features": {
        "auto_backup": true,
        "backup_interval": 3600,
        "max_search_results": 20,
        "pagination_size": 10,
        "image_validation": false,
        "related_item_search": true,
        "fuzzy_search": true,
        "enable_admin_commands": true,
        "admin_role_name": "Bot管理者",
        "allowed_channels": []
    },
    "database": {
        "path": "data/items.db",
        "backup_dir": "backups",
        "max_backups": 5
    },
    "logging": {
        "level": "INFO",
        "file": "logs/bot.log",
        "max_size": 10485760,
        "backup_count": 5
    }
}
```

## 5. 技術仕様

### 使用技術
- Python 3.9+
- discord.py 2.0+
- aiosqlite（非同期SQLite）
- jaconv（日本語変換）
- aiohttp（非同期HTTP）

### ファイル構成
```
/app/product/DA_discord/
├── src/
│   ├── main.py          # メインエントリー
│   ├── database.py      # データベース管理
│   ├── search_engine.py # 検索エンジン
│   ├── embed_manager.py # Embed生成
│   ├── npc_parser.py    # NPC交換データ解析
│   └── constants.py     # 共通定数
├── data/
│   └── items.db         # SQLiteデータベース
├── logs/
│   └── bot.log          # ログファイル
├── backups/             # バックアップディレクトリ
├── ref/                 # 仕様書・設計書
└── config.json          # 設定ファイル
```

## 6. 今後の拡張予定

1. **お気に入り機能**
   - ユーザーごとのお気に入りアイテム登録
   - お気に入り一覧表示

2. **検索履歴・統計機能**
   - 個人の検索履歴表示
   - 人気アイテムランキング

3. **高度な検索機能**
   - 複数条件検索
   - レベル範囲指定
   - エリア指定検索