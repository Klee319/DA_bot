# 未実装テーブルの設計仕様書

## 1. 採集場所テーブル (gathering_locations)

### 目的
素材アイテムの採集場所と方法の詳細情報を管理

### テーブル構造
```sql
CREATE TABLE gathering_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,                    -- 採集できるアイテム名
    location_name TEXT NOT NULL,                -- 採集場所名
    category TEXT NOT NULL,                     -- 採集カテゴリ（採取/採掘/釣り）
    method TEXT,                                -- 採集方法の詳細
    coordinates TEXT,                           -- 座標情報（あれば）
    required_tool TEXT,                         -- 必要な道具
    required_level INTEGER,                     -- 必要レベル
    success_rate REAL,                          -- 成功率（0.0-1.0）
    respawn_time INTEGER,                       -- リスポーン時間（分）
    available_time TEXT,                        -- 利用可能時間
    notes TEXT,                                 -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### インデックス
```sql
CREATE INDEX idx_gathering_locations_item_name ON gathering_locations(item_name);
CREATE INDEX idx_gathering_locations_category ON gathering_locations(category);
CREATE INDEX idx_gathering_locations_location ON gathering_locations(location_name);
```

### サンプルデータ
```sql
INSERT INTO gathering_locations VALUES 
(1, '石', '山岳地帯', '採掘', 'つるはしで採掘', '123,456', 'つるはし', 1, 0.8, 30, '24時間', NULL),
(2, '木材', '森林エリア', '採取', '斧で伐採', '234,567', '斧', 1, 0.9, 45, '06:00-18:00', NULL),
(3, '魚', '湖畔', '釣り', '釣り竿で釣り上げ', '345,678', '釣り竿', 5, 0.6, 15, '05:00-21:00', '雨天時成功率UP');
```

## 2. NPCテーブル (npcs)

### 目的
NPCの交換・購入・クエスト情報を管理

### テーブル構造
```sql
CREATE TABLE npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_name TEXT NOT NULL,                     -- NPC名
    location TEXT NOT NULL,                     -- NPC所在地
    npc_type TEXT NOT NULL,                     -- NPC種別（商人/クエスト/交換/ギルド）
    shop_items TEXT,                            -- 販売アイテムリスト（JSON形式）
    exchange_items TEXT,                        -- 交換アイテムリスト（JSON形式）
    quest_items TEXT,                           -- クエスト関連アイテム（JSON形式）
    available_hours TEXT,                       -- 営業時間
    required_reputation INTEGER,               -- 必要好感度
    guild_level INTEGER,                        -- 必要ギルドレベル
    description TEXT,                           -- NPC説明
    notes TEXT,                                 -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### インデックス
```sql
CREATE INDEX idx_npcs_name ON npcs(npc_name);
CREATE INDEX idx_npcs_type ON npcs(npc_type);
CREATE INDEX idx_npcs_location ON npcs(location);
```

### JSON構造例
```json
// shop_items例
[
  {"item": "石", "price": 10, "currency": "Gold", "stock": 999},
  {"item": "木材", "price": 15, "currency": "Gold", "stock": 50}
]

// exchange_items例
[
  {"give": [{"item": "鉄鉱石", "quantity": 5}], "receive": [{"item": "鉄インゴット", "quantity": 1}]},
  {"give": [{"item": "古い装備", "quantity": 1}], "receive": [{"item": "修理キット", "quantity": 1}]}
]

// quest_items例
[
  {"quest": "素材収集", "required": [{"item": "石", "quantity": 10}], "reward": [{"item": "経験値", "quantity": 100}]}
]
```

### サンプルデータ
```sql
INSERT INTO npcs VALUES 
(1, '武器商人ジョン', '町の中央広場', '商人', 
 '[{"item":"石","price":10,"currency":"Gold","stock":999}]',
 '[{"give":[{"item":"鉄鉱石","quantity":5}],"receive":[{"item":"鉄インゴット","quantity":1}]}]',
 NULL, '09:00-18:00', 0, NULL, '武器と素材を扱う商人', NULL),
(2, 'ギルドマスター', 'ギルドホール', 'ギルド', NULL,
 '[{"give":[{"item":"ギルドポイント","quantity":100}],"receive":[{"item":"特別装備","quantity":1}]}]',
 '[{"quest":"討伐依頼","required":[{"item":"ゴブリンの証","quantity":5}],"reward":[{"item":"Gold","quantity":500}]}]',
 '24時間', 0, 1, 'ギルドクエストを管理', NULL);
```

## 3. 実装優先度と依存関係

### Phase 1: 採集場所テーブル
- **優先度**: 高
- **理由**: 素材の入手元詳細で最も需要が高い
- **依存関係**: なし（独立して実装可能）

### Phase 2: NPCテーブル
- **優先度**: 中
- **理由**: 交換・購入情報の提供
- **依存関係**: ゲーム内のNPC情報収集が必要

## 4. 実装時の考慮事項

### データ収集方法
1. **採集場所**: プレイヤーからの情報提供、ゲーム内探索
2. **NPC情報**: 既存のwiki情報、プレイヤー報告

### UI/UX考慮
1. **採集場所**: 地図との連携可能性を考慮
2. **NPC**: 交換レート計算機能の検討

### 技術的考慮
1. **JSON形式**: 複雑な関係性を柔軟に表現
2. **インデックス**: 検索性能の最適化
3. **更新頻度**: ゲームアップデートによる情報変更への対応

## 5. 実装タスク一覧

### 採集場所テーブル実装
- [ ] テーブル作成SQLの実行
- [ ] サンプルデータの投入
- [ ] search_engine.py の `_search_gathering_locations` メソッド実装
- [ ] embed_manager.py での採集場所情報表示機能
- [ ] CSV一括インポート機能
- [ ] 管理画面での採集場所追加・編集機能

### NPCテーブル実装
- [ ] テーブル作成SQLの実行
- [ ] JSON形式での複雑なデータ管理ロジック
- [ ] search_engine.py の `_search_npc_sources` メソッド実装
- [ ] embed_manager.py でのNPC情報表示機能
- [ ] 交換レート計算機能
- [ ] クエスト情報との連携

## 6. テスト計画

### 単体テスト
- [ ] 各検索メソッドの動作確認
- [ ] JSON データの解析・表示テスト
- [ ] エラーハンドリングの確認

### 統合テスト
- [ ] 素材詳細画面での統合表示テスト
- [ ] ページネーションとの連携確認
- [ ] パフォーマンステスト（大量データでの動作確認）