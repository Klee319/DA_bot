# Discord DA アイテム参照BOT

Discord上で動作する日本語アイテム検索BOT。ゲーム内の装備・素材・モンスター・NPC・採集情報を簡単に検索できます。

## 主な機能

### 🔍 高度な検索機能
- **統合検索**: 装備、素材、モンスター、NPC、採集場所を一括検索
- **ワイルドカード対応**: `*破片`のような柔軟な検索が可能
- **レベル/ランク自動除去**: 「グロースクリスタルLv1」→「グロースクリスタル*」を自動検索
- **表記ゆれ対応**: ひらがな・カタカナ・漢字・全角半角を自動変換

### 📊 リッチな表示
- **Embed形式**: 見やすいカード形式で情報表示
- **インタラクティブUI**: プルダウンメニューやボタンで詳細情報にアクセス
- **画像対応**: アイテム画像のサムネイル表示
- **関連情報表示**: 入手元・利用先・ドロップアイテムなどを表示

### 🛡️ 管理機能
- **権限管理**: 管理者ロール・ユーザー指定
- **チャンネル制限**: 特定チャンネルでのみ使用可能に設定
- **データベース管理**: CSVからの一括更新、自動バックアップ

## セットアップ

### 必要環境
- Python 3.9以上
- Discord Bot Token

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/Klee319/DA_bot.git
cd DA_bot
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 設定ファイルを作成
```bash
cp config.example.json config.json
```

4. `config.json`を編集してBot Tokenを設定
```json
{
    "bot": {
        "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
        "prefix": "!",
        "owner_id": "YOUR_DISCORD_USER_ID_HERE"
    }
}
```

5. Botを起動
```bash
python src/main.py
```

## 使い方

### 基本コマンド

#### アイテム検索
```
!da <検索キーワード>
```

例：
- `!da グロースクリスタル` - グロースクリスタルを検索
- `!da *破片` - 「○○破片」という名前のアイテムをすべて検索
- `!da スライム` - スライムというモンスターを検索

### 管理者コマンド（Bot管理者ロールまたは指定ユーザーのみ）

#### データベース更新
```
!da-update
```
CSVファイルを添付してデータベースを更新

#### バックアップ作成
```
!da-backup
```
現在のデータベースをバックアップ

#### 設定再読み込み
```
!da-reload
```
config.jsonを再読み込み

#### 管理者ロール管理
```
!da-admin-role-add @ロール名
!da-admin-role-remove @ロール名
!da-admin-role-list
```

#### チャンネル制限管理
```
!da-channel-add #チャンネル名
!da-channel-remove #チャンネル名
!da-channel-list
```

## 設定

### config.json の詳細

```json
{
    "bot": {
        "token": "Discord Bot Token",
        "prefix": "!",              // コマンドプレフィックス
        "owner_id": "所有者のDiscord ID"
    },
    "features": {
        "auto_backup": true,        // 自動バックアップ
        "backup_interval": 3600,    // バックアップ間隔（秒）
        "max_search_results": 20,   // 最大検索結果数
        "pagination_size": 10,      // ページあたりの表示数
        "image_validation": false,  // 画像URL検証
        "related_item_search": true,// 関連アイテム検索
        "fuzzy_search": true,       // あいまい検索
        "enable_admin_commands": true, // 管理コマンド有効化
        "admin_role_name": "Bot管理者",  // 管理者ロール名
        "allowed_channels": []      // 使用可能チャンネルID（空=全チャンネル）
    },
    "database": {
        "path": "data/items.db",    // データベースパス
        "backup_dir": "backups",    // バックアップディレクトリ
        "max_backups": 5           // 最大バックアップ数
    },
    "logging": {
        "level": "INFO",           // ログレベル
        "file": "logs/bot.log",    // ログファイル
        "max_size": 10485760,      // 最大サイズ（10MB）
        "backup_count": 5          // ログファイル世代数
    }
}
```

## データベース構造

### テーブル一覧
- **equipments**: 装備品情報
- **materials**: 素材情報  
- **mobs**: モンスター情報
- **npcs**: NPC情報
- **gatherings**: 採集場所情報
- **admin_roles**: 管理者ロール（動的管理）
- **admin_users**: 管理者ユーザー（動的管理）
- **user_favorites**: お気に入り（未実装）
- **search_history**: 検索履歴（未実装）
- **search_stats**: 検索統計（未実装）

### CSV形式

各テーブルに対応するCSVファイルの形式：

#### equipments.csv
```csv
正式名称,一般名称,入手場所,入手カテゴリ,種類,必要素材,必要レベル,アイテム効果,一言,画像リンク
```

#### materials.csv
```csv
正式名称,一般名称,入手カテゴリ,入手方法,利用カテゴリ,使用用途,一言,画像リンク
```

#### mobs.csv
```csv
正式名称,一般名称,出没エリア,出没エリア詳細,必要レベル,ドロップ品,EXP,Gold,必要守備力,一言,画像リンク
```

#### gatherings.csv
```csv
場所,収集方法,入手素材,使用用途,必要ツール,一言,画像リンク
```

#### npcs.csv
```csv
場所,NPC名,業種,入手アイテム,必要素材,EXP,Gold,一言,画像パス
```

## 開発

### ディレクトリ構造
```
DA_bot/
├── src/                    # ソースコード
│   ├── main.py            # メインエントリー
│   ├── database.py        # データベース管理
│   ├── search_engine.py   # 検索エンジン
│   ├── embed_manager.py   # Embed生成
│   ├── npc_parser.py      # NPC交換データ解析
│   └── constants.py       # 共通定数
├── data/                  # データファイル
│   └── items.db          # SQLiteデータベース
├── logs/                  # ログファイル
├── backups/              # バックアップ
├── ref/                  # 仕様書・設計書
│   ├── specification_v2.md    # 最新仕様書
│   ├── task_management.md     # タスク管理書
│   └── npc_exchange_specification.md
└── tests/                # テストコード
```

### 主な特徴

#### ワイルドカード検索
- 前方一致: `*破片` → ○○破片
- 後方一致: `グロースクリスタル*` → グロースクリスタル○○
- 中間一致: `【圧縮】*` → 【圧縮】○○

#### レベル/ランク除去
以下のパターンを自動的に除去：
- Lv○○, Lv.○○
- レベル○○
- ランク○○, Rank○○
- ★○○
- 末尾の数字

#### 表記ゆれ対応
- ひらがな ⇔ カタカナ ⇔ 漢字
- 全角 ⇔ 半角
- よくある誤字（づ/ず、ぢ/じ等）

## トラブルシューティング

### よくある問題

**Q: Botが反応しない**
- Bot Tokenが正しく設定されているか確認
- Botに必要な権限があるか（メッセージ送信、Embed送信、リアクション追加）
- `allowed_channels`が設定されている場合、正しいチャンネルで使用しているか

**Q: 検索結果が表示されない**
- データベースが正しく初期化されているか確認
- CSVファイルが正しくインポートされているか
- ログファイルでエラーを確認

**Q: ワイルドカードアイテムが表示されない**
- モブのドロップにワイルドカードアイテムも含まれるようになりました
- `*破片`のようなアイテムも正しく検索・表示されます

## 今後の実装予定

- お気に入り機能（user_favorites）
- 検索履歴機能（search_history）
- 検索統計・ランキング（search_stats）
- 高度な検索（複数条件、レベル範囲指定等）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能提案は[Issues](https://github.com/Klee319/DA_bot/issues)にお願いします。

プルリクエストも歓迎します！

## 作者

- GitHub: [@Klee319](https://github.com/Klee319)

## 謝辞

このBotは[Claude Code](https://claude.ai/code)の支援を受けて開発されました。

---

📝 **注意**: このBOTは特定のゲーム向けに開発されています。使用する際は対象ゲームの利用規約を確認してください。