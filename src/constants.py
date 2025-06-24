# -*- coding: utf-8 -*-
"""共通定数定義"""

# ワイルドカード文字
WILDCARD_CHARS = ('*', '?', '＊', '？')
WILDCARD_SET = set(WILDCARD_CHARS)

# Discord API制限
DISCORD_SELECT_MAX_OPTIONS = 25
DISCORD_EMBED_MAX_FIELDS = 25
DISCORD_BUTTON_MAX_COUNT = 5

# ページネーション
DEFAULT_PAGE_SIZE = 10
MAX_SEARCH_RESULTS = 20

# タイムアウト
VIEW_TIMEOUT = 600  # 10分

# データベーステーブル
ITEM_TABLES = ['equipments', 'materials', 'mobs']
ALL_TABLES = ['equipments', 'materials', 'mobs', 'npcs', 'gatherings']