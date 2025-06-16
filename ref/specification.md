# Discord アイテム参照BOT 仕様書

## 1. プロジェクト概要

### 1.1 目的
Discord上でCSVデータに基づいたアイテム情報を検索・表示し、ユーザー間でのアイテム情報共有を円滑にするBOTの開発。

### 1.2 主要機能
- アイテム検索機能（完全一致・ワイルドカード検索・表記ゆれ対応）
- インタラクティブなアイテム情報表示（Embed + ボタン）
- CSV管理機能（アップロード・バリデーション・バックアップ）
- ユーザー機能（お気に入り・検索履歴）
- 管理者機能（統計情報・ログ管理）

## 2. 技術スタック

### 2.1 開発環境
- **Python**: 3.10以上
- **メインライブラリ**: discord.py 2.3.x
- **データベース**: SQLite3
- **データ処理**: pandas
- **日本語処理**: jaconv
- **設定管理**: JSON形式

### 2.2 依存関係
```
discord.py==2.3.2
pandas>=2.0.0
jaconv>=0.3.0
aiohttp>=3.8.0
pillow>=9.0.0
```

## 3. データベース設計

### 3.1 テーブル構造

#### 3.1.1 equipments テーブル
```sql
CREATE TABLE equipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL UNIQUE,
    common_name TEXT,
    acquisition_category TEXT,
    type TEXT,
    required_materials TEXT,
    required_level INTEGER,
    item_effect TEXT,
    description TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 materials テーブル
```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL UNIQUE,
    common_name TEXT,
    acquisition_category TEXT,
    type TEXT,
    required_materials TEXT,
    required_level INTEGER,
    item_effect TEXT,
    description TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.3 mobs テーブル
```sql
CREATE TABLE mobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formal_name TEXT NOT NULL UNIQUE,
    common_name TEXT,
    area TEXT,
    area_detail TEXT,
    required_level INTEGER,
    drops TEXT,
    exp INTEGER,
    gold INTEGER,
    required_defense INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.4 gatherings テーブル
```sql
CREATE TABLE gatherings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    collection_method TEXT,
    obtained_materials TEXT,
    usage TEXT,
    required_tools TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.5 user_favorites テーブル
```sql
CREATE TABLE user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    item_name TEXT NOT NULL,
    item_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, item_name, item_type)
);
```

#### 3.1.6 search_history テーブル
```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    result_count INTEGER,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.7 search_stats テーブル
```sql
CREATE TABLE search_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    search_count INTEGER DEFAULT 1,
    last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(item_name)
);
```

### 3.2 正規化とインデックス
```sql
-- 検索性能向上のためのインデックス
CREATE INDEX idx_equipments_formal_name ON equipments(formal_name);
CREATE INDEX idx_equipments_common_name ON equipments(common_name);
CREATE INDEX idx_materials_formal_name ON materials(formal_name);
CREATE INDEX idx_materials_common_name ON materials(common_name);
CREATE INDEX idx_mobs_formal_name ON mobs(formal_name);
CREATE INDEX idx_mobs_common_name ON mobs(common_name);

-- 履歴とお気に入りのインデックス
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_searched_at ON search_history(searched_at);
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
```

## 4. 機能仕様

### 4.1 検索機能

#### 4.1.1 検索アルゴリズム
1. **優先順位**:
   - 正式名称の完全一致
   - 一般名称の完全一致
   - ワイルドカード検索（`*`、`?`）
   - 表記ゆれ対応検索

2. **表記ゆれ正規化**:
   ```python
   def normalize_text(text):
       # 全角→半角変換
       text = jaconv.z2h(text, kana=True, ascii=True, digit=True)
       # カタカナ→ひらがな変換
       text = jaconv.kata2hira(text)
       # 大文字→小文字変換
       text = text.lower()
       return text
   ```

3. **複数アイテム検索**: 最大3つまでの同時検索対応

#### 4.1.2 検索結果表示
- **単一結果**: 詳細情報をEmbedで表示
- **複数結果**: ページネーション付き一覧表示
- **アイテム名リンク**: クリックで詳細情報表示

### 4.2 CSV管理機能

#### 4.2.1 アップロード機能
- **権限**: 管理者のみ
- **コマンド**: `/upload_csv [type] [file]`
- **対応形式**: equipment, material, mob, gathering

#### 4.2.2 バリデーション
```python
def validate_csv(df, csv_type):
    required_columns = {
        'equipment': ['正式名称', '一般名称'],
        'material': ['正式名称', '一般名称'],
        'mob': ['正式名称', '一般名称'],
        'gathering': ['場所', '収集方法']
    }
    
    # 必須カラムチェック
    # 正式名称の重複チェック
    # データ型検証
    return validation_result
```

#### 4.2.3 バックアップ機能
- **自動バックアップ**: 更新前にタイムスタンプ付きでバックアップ
- **保存場所**: `./backups/YYYYMMDD_HHMMSS_[table_name].db`

### 4.3 ユーザー機能

#### 4.3.1 お気に入り機能
- **追加**: アイテム詳細画面の「⭐お気に入り追加」ボタン
- **削除**: お気に入り一覧の「❌削除」ボタン
- **一覧表示**: `/favorites`コマンド

#### 4.3.2 検索履歴
- **自動記録**: 検索実行時に自動保存
- **保存期間**: 30日間
- **表示**: `/history`コマンド

### 4.4 インタラクション機能

#### 4.4.1 Embedデザイン
```python
def create_item_embed(item_data, item_type):
    embed = discord.Embed(
        title=f"🔍 {item_data['formal_name']}",
        color=get_type_color(item_type)
    )
    
    # null値のフィールドは除外
    for field, value in item_data.items():
        if value and value != 'null':
            embed.add_field(name=field, value=value, inline=True)
    
    # 画像URL有効性チェック後に設定
    if item_data['image_url'] and is_valid_image_url(item_data['image_url']):
        embed.set_image(url=item_data['image_url'])
    
    return embed
```

#### 4.4.2 ボタンコンポーネント
```python
class ItemView(discord.ui.View):
    def __init__(self, item_data, timeout=300):
        super().__init__(timeout=timeout)
        
    @discord.ui.button(label="⭐お気に入り追加", style=discord.ButtonStyle.primary)
    async def add_favorite(self, interaction, button):
        # お気に入り追加処理
        
    @discord.ui.button(label="🔗関連アイテム", style=discord.ButtonStyle.secondary)
    async def show_related(self, interaction, button):
        # 関連アイテム表示処理
```

### 4.5 管理機能

#### 4.5.1 統計情報
- **検索ランキング**: `/stats search_ranking`
- **ユーザー統計**: `/stats user_activity`
- **システム情報**: `/stats system`

#### 4.5.2 ログ管理
- **エラーログ**: 管理者が指定したチャンネルに出力
- **操作ログ**: CSV更新、設定変更などの記録

## 5. 設定ファイル仕様

### 5.1 config.json
```json
{
  "bot": {
    "token": "環境変数から取得",
    "command_prefix": "!",
    "activity": "アイテム検索中..."
  },
  "database": {
    "path": "./data/items.db",
    "backup_path": "./backups/"
  },
  "csv_mapping": {
    "equipment": {
      "正式名称": "formal_name",
      "一般名称": "common_name",
      "入手カテゴリ": "acquisition_category",
      "種類": "type",
      "必要素材": "required_materials",
      "必要レベル": "required_level",
      "アイテム効果": "item_effect",
      "一言": "description",
      "画像リンク": "image_url"
    },
    "material": {
      "正式名称": "formal_name",
      "一般名称": "common_name",
      "入手カテゴリ": "acquisition_category",
      "種類": "type",
      "必要素材": "required_materials",
      "必要レベル": "required_level",
      "アイテム効果": "item_effect",
      "一言": "description",
      "画像リンク": "image_url"
    },
    "mob": {
      "正式名称": "formal_name",
      "一般名称": "common_name",
      "出没エリア": "area",
      "出没エリア詳細": "area_detail",
      "必要レベル": "required_level",
      "ドロップ品": "drops",
      "EXP": "exp",
      "Gold": "gold",
      "必要守備力": "required_defense",
      "一言": "description"
    },
    "gathering": {
      "場所": "location",
      "収集方法": "collection_method",
      "入手素材": "obtained_materials",
      "使用用途": "usage",
      "必要ツール": "required_tools",
      "一言（あれば）": "description"
    }
  },
  "permissions": {
    "admin_users": [],
    "admin_roles": [],
    "log_channel_id": null
  },
  "features": {
    "max_search_items": 3,
    "search_history_days": 30,
    "pagination_size": 10,
    "image_validation": true,
    "auto_backup": true
  }
}
```

## 6. ユースケース

### 6.1 基本的な検索フロー
1. ユーザーが「木の棒」と投稿
2. BOTが正式名称で完全一致検索実行
3. 結果が見つかった場合、詳細情報をEmbedで表示
4. 関連アイテム（必要素材、ドロップ元）をリンク化
5. お気に入りボタンで登録可能

### 6.2 管理者のCSV更新フロー
1. 管理者が`/upload_csv equipment equipment.csv`実行
2. BOTがCSVの形式・内容をバリデーション
3. 問題なければ自動バックアップ作成
4. SQLiteデータベースを更新
5. 完了メッセージを返信

### 6.3 ワイルドカード検索フロー
1. ユーザーが「木*」と投稿
2. BOTが「木」で始まるアイテムを検索
3. 複数結果をページネーション形式で表示
4. 各アイテム名がクリック可能なリンクとして表示

## 7. エラーハンドリング

### 7.1 主要エラーパターン
- **アイテム未発見**: 「アイテムが存在しないかデータが作成されていません」
- **CSV形式エラー**: 詳細なエラー内容を管理者に通知
- **データベースエラー**: ログ記録と自動復旧試行
- **API制限エラー**: レート制限の適切な処理

### 7.2 例外処理戦略
```python
async def safe_search(query):
    try:
        result = await search_item(query)
        return result
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return "データベースエラーが発生しました"
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return "検索クエリが無効です"
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        return "予期しないエラーが発生しました"
```

## 8. パフォーマンス要件

### 8.1 応答時間
- **基本検索**: 500ms以内
- **複雑な検索**: 2秒以内
- **CSV更新**: 10秒以内（10,000レコードまで）

### 8.2 同時処理
- **同時検索**: 100件まで
- **非同期処理**: インタラクション中の新規クエリ無効化

## 9. セキュリティ仕様

### 9.1 権限管理
- **管理者権限**: Discord Role または User ID ベース
- **コマンド制限**: 管理者専用コマンドの適切な制限

### 9.2 データ保護
- **トークン管理**: 環境変数での管理必須
- **SQLインジェクション**: パラメータ化クエリの使用
- **ファイルアップロード**: 拡張子とMIMEタイプの検証

## 10. 実装優先度

### Phase 1 (高優先度)
- [ ] 基本的なアイテム検索機能
- [ ] SQLiteデータベース設計・構築
- [ ] CSV読み込み機能
- [ ] 基本的なEmbed表示

### Phase 2 (中優先度)
- [ ] ワイルドカード検索
- [ ] 表記ゆれ対応
- [ ] インタラクティブボタン
- [ ] ページネーション

### Phase 3 (低優先度)
- [ ] お気に入り機能
- [ ] 検索履歴
- [ ] 統計機能
- [ ] 管理機能

この仕様書に基づいて、段階的な開発を実施し、各フェーズごとに動作確認とテストを行うことを推奨します。