import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import json
import os
import signal
import sys
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

from database import DatabaseManager
from search_engine import SearchEngine
from embed_manager import EmbedManager, LocationAcquisitionView
from csv_manager import CSVManager

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ItemReferenceBot(commands.Bot):
    def __init__(self):
        # 設定を読み込み
        self.config = self.load_config()
        
        # Intentsの設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=self.config['bot']['command_prefix'],
            intents=intents,
            help_command=None
        )
        
        # コマンドプレフィックスを保存
        self.command_prefix = self.config['bot']['command_prefix']
        logger.info(f"コマンドプレフィックス: '{self.command_prefix}'")
        
        # コンポーネントの初期化
        self.db_manager = DatabaseManager(self.config['database']['path'])
        self.search_engine = SearchEngine(self.db_manager, self.config)
        self.embed_manager = EmbedManager(self.config)
        self.csv_manager = CSVManager(self.db_manager, self.config)
        
        # 処理済みメッセージIDのセット（重複防止用）
        self.processed_messages = set()
        # 処理中のメッセージIDのセット（同時処理防止用）
        self.processing_messages = set()
        # 古いメッセージIDを定期的にクリア（メモリ節約）
        self.last_cleanup = asyncio.get_event_loop().time()
        
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 環境変数から値を設定
            if os.getenv('DISCORD_TOKEN'):
                config['bot']['token'] = os.getenv('DISCORD_TOKEN')
            
            if os.getenv('ADMIN_USER_IDS'):
                admin_ids = os.getenv('ADMIN_USER_IDS').split(',')
                config['permissions']['admin_users'] = [int(uid.strip()) for uid in admin_ids]
            
            if os.getenv('ADMIN_ROLE_IDS'):
                admin_role_ids = os.getenv('ADMIN_ROLE_IDS').split(',')
                config['permissions']['admin_roles'] = [int(rid.strip()) for rid in admin_role_ids]
            
            if os.getenv('LOG_CHANNEL_ID'):
                config['permissions']['log_channel_id'] = int(os.getenv('LOG_CHANNEL_ID'))
            
            return config
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗: {e}")
            raise
    
    async def setup_hook(self):
        """Bot起動時の初期化処理"""
        try:
            # データベースの初期化
            await self.db_manager.initialize_database()
            
            # スラッシュコマンドを同期
            await self.tree.sync()
            logger.info("スラッシュコマンドの同期が完了しました")
            
            logger.info("BOTの初期化が完了しました")
        except Exception as e:
            logger.error(f"BOTの初期化に失敗: {e}")
            raise
    
    async def on_ready(self):
        """Bot準備完了時の処理"""
        import os
        logger.info(f'[PID:{os.getpid()}] {self.user} として接続しました')
        logger.info(f'Discord.py version: {discord.__version__}')
        logger.info(f'接続サーバー数: {len(self.guilds)}')
        
        # アクティビティの設定（Bot準備完了後に実行）
        try:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config['bot']['activity']
            )
            await self.change_presence(activity=activity)
            logger.info("プレゼンス設定が完了しました")
        except Exception as e:
            logger.error(f"プレゼンス設定に失敗: {e}")
    
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        # Botからのメッセージは無視
        if message.author.bot:
            return
        
        # 既に処理済みまたは処理中のメッセージは無視（重複防止）
        if message.id in self.processed_messages or message.id in self.processing_messages:
            import os
            logger.info(f"[PID:{os.getpid()}] 重複メッセージスキップ: {message.id}")
            return
        
        # メッセージIDを処理中リストに追加
        self.processing_messages.add(message.id)
        
        try:
            # 定期的にセットをクリア（1000件ごと）
            if len(self.processed_messages) > 1000:
                self.processed_messages.clear()
                self.processing_messages.clear()
            
            # コマンドプレフィックスのチェック
            ctx = await self.get_context(message)
            
            # コマンドが見つかった場合はコマンドを実行
            if ctx.valid:
                await self.invoke(ctx)
            # コマンドでない場合のみアイテム検索を実行
            elif not message.content.startswith(self.command_prefix):
                # チャンネル制限チェック（ホワイトリスト制）
                allowed_channels = self.config['permissions']['allowed_channels']
                
                # 許可チャンネルリストが空の場合は、BOTが動作しない
                if not allowed_channels:
                    # 管理者権限を持つユーザーには案内メッセージを表示
                    user_roles = [role.id for role in message.author.roles] if hasattr(message.author, 'roles') and message.author.roles else []
                    if self.is_admin(message.author.id, user_roles):
                        await message.reply("⚠️ BOT利用可能チャンネルが設定されていません。\n`/add_allowed_channel` コマンドでチャンネルを追加してください。", mention_author=False)
                    return
                
                # 現在のチャンネルが許可リストに含まれているかチェック
                if message.channel.id not in allowed_channels:
                    return
                
                await self.handle_item_search(message)
                
        finally:
            # 処理完了後にメッセージIDを処理済みに移動
            self.processing_messages.discard(message.id)
            self.processed_messages.add(message.id)
    
    async def handle_item_search(self, message):
        """アイテム検索を処理"""
        try:
            query = message.content.strip()
            if not query:
                return
            
            # デバッグログ追加（プロセスIDも含める）
            import os
            logger.info(f"[PID:{os.getpid()}] アイテム検索開始: '{query}' from {message.author}")
            
            # 入手手段と場所の定義
            acquisition_methods = ['クエスト', '購入', '交換', 'モブ', '採取', '採掘', '釣り']
            locations = ['レポロ', 'マクルダ', 'ルーチェア', 'ソルソロ', 'サプネラ', 'セシド']
            
            # 入力が入手手段または場所に一致するかチェック
            if query in acquisition_methods:
                await self.handle_acquisition_method_query(message, query, locations)
                return
            elif query in locations:
                await self.handle_location_query(message, query, acquisition_methods)
                return
            
            # 複数アイテム検索をサポート（最大3つ）
            queries = [q.strip() for q in query.split() if q.strip()]
            queries = queries[:self.config['features']['max_search_items']]
            
            results = []
            for q in queries:
                search_results = await self.search_engine.search(q)
                if search_results:
                    results.extend(search_results)
                    # 検索統計を更新
                    await self.db_manager.update_search_stats(q)
            
            # 検索履歴を追加
            await self.db_manager.add_search_history(
                str(message.author.id), 
                query, 
                len(results)
            )
            
            if results:
                if len(results) == 1:
                    # 単一結果の場合は詳細表示
                    embed, view = await self.embed_manager.create_item_detail_embed(
                        results[0], str(message.author.id)
                    )
                    await message.reply(embed=embed, view=view, mention_author=False)
                else:
                    # 複数結果の場合はリスト表示
                    embed, view = await self.embed_manager.create_search_results_embed(
                        results, query, page=0
                    )
                    await message.reply(embed=embed, view=view, mention_author=False)
            else:
                # より詳細なメッセージを提供
                if len(query.strip()) < 2:
                    await message.reply("検索文字は2文字以上で入力してください", mention_author=False, delete_after=10)
                else:
                    suggestions = await self.search_engine.get_search_suggestions(query.strip()[:20], 5)
                    if suggestions:
                        embed = discord.Embed(
                            title="**アイテムが見つかりませんでした**",
                            description=f"「{query}」に一致するアイテムはありません",
                            color=discord.Color.orange()
                        )
                        embed.add_field(
                            name="**候補**",
                            value="\n".join([f"- {suggestion}" for suggestion in suggestions]),
                            inline=False
                        )
                        await message.reply(embed=embed, mention_author=False)
                    else:
                        await message.reply("アイテムが存在しないかデータが作成されていません", mention_author=False, delete_after=10)
                
        except Exception as e:
            logger.error(f"アイテム検索エラー: {e}")
            # ユーザーに分かりやすいエラーメッセージ
            embed = discord.Embed(
                title="**エラーが発生しました**",
                description="検索処理中に問題が発生しました。しばらく時間をおいて再度お試しください。",
                color=discord.Color.red()
            )
            embed.add_field(
                name="**ヒント**",
                value="- 検索文字を短くしてみてください\n- 特殊文字を使わないでください\n- しばらく時間をおいて再度お試しください",
                inline=False
            )
            await message.reply(embed=embed, mention_author=False)
    
    def is_admin(self, user_id: int, user_roles: List[int] = None) -> bool:
        """管理者権限をチェック（ユーザーIDまたはロールで判定）"""
        # ユーザーIDでチェック
        if user_id in self.config['permissions']['admin_users']:
            return True
        
        # ロールでチェック
        if user_roles:
            admin_roles = self.config['permissions']['admin_roles']
            for role_id in user_roles:
                if role_id in admin_roles:
                    return True
        
        return False
    
    def is_admin_interaction(self, interaction: discord.Interaction) -> bool:
        """Interactionから管理者権限をチェック"""
        user_id = interaction.user.id
        user_roles = [role.id for role in interaction.user.roles] if hasattr(interaction.user, 'roles') and interaction.user.roles else []
        return self.is_admin(user_id, user_roles)
    
    async def on_command_error(self, ctx, error):
        """コマンドエラー処理"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply("このコマンドを実行する権限がありません")
        else:
            logger.error(f"コマンドエラー: {error}")
            await ctx.reply("コマンド実行中にエラーが発生しました")
    
    async def handle_acquisition_method_query(self, message, acquisition_method, locations):
        """入手手段が入力された時の処理"""
        embed = discord.Embed(
            title=f"**{acquisition_method}** の場所を選択してください",
            description="下のメニューから町を選んでください",
            color=discord.Color.blue()
        )
        
        # 選択肢を作成
        options = []
        for location in locations:
            options.append(discord.SelectOption(
                label=location,
                value=f"{acquisition_method}_{location}",
                description=f"{location}の{acquisition_method}"
            ))
        
        # Viewを作成
        view = LocationAcquisitionView(options, acquisition_method, None, self.embed_manager, self.search_engine)
        await message.reply(embed=embed, view=view, mention_author=False)
    
    async def handle_location_query(self, message, location, acquisition_methods):
        """場所が入力された時の処理"""
        embed = discord.Embed(
            title=f"**{location}** の入手手段を選択してください",
            description="下のメニューからジャンルを選んでください",
            color=discord.Color.green()
        )
        
        # 選択肢を作成
        options = []
        for method in acquisition_methods:
            options.append(discord.SelectOption(
                label=method,
                value=f"{method}_{location}",
                description=f"{location}の{method}"
            ))
        
        # Viewを作成
        view = LocationAcquisitionView(options, None, location, self.embed_manager, self.search_engine)
        await message.reply(embed=embed, view=view, mention_author=False)

# コマンドクラス
class ItemCommands(commands.Cog):
    def __init__(self, bot: ItemReferenceBot):
        self.bot = bot
    
    @commands.command(name='favorites', aliases=['fav'])
    async def show_favorites(self, ctx):
        """お気に入りアイテム一覧を表示"""
        try:
            favorites = await self.bot.db_manager.get_user_favorites(str(ctx.author.id))
            
            if not favorites:
                await ctx.reply("お気に入りアイテムが登録されていません")
                return
            
            embed, view = await self.bot.embed_manager.create_favorites_embed(
                favorites, ctx.author.id
            )
            await ctx.reply(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"お気に入り表示エラー: {e}")
            await ctx.reply("お気に入り表示中にエラーが発生しました")
    
    @commands.command(name='history')
    async def show_history(self, ctx):
        """検索履歴を表示"""
        try:
            history = await self.bot.db_manager.get_search_history(
                str(ctx.author.id), 
                self.bot.config['features']['search_history_days']
            )
            
            if not history:
                await ctx.reply("検索履歴がありません")
                return
            
            embed = await self.bot.embed_manager.create_history_embed(history)
            await ctx.reply(embed=embed)
            
        except Exception as e:
            logger.error(f"履歴表示エラー: {e}")
            await ctx.reply("履歴表示中にエラーが発生しました")

class AdminCommands(commands.Cog):
    def __init__(self, bot: ItemReferenceBot):
        self.bot = bot
    
    @app_commands.command(name='upload_csv', description='CSVファイルをアップロードしてデータベースを更新')
    @app_commands.describe(
        csv_type='アップロードするCSVの種類',
        csv_file='アップロードするCSVファイル'
    )
    @app_commands.choices(csv_type=[
        app_commands.Choice(name='装備', value='equipment'),
        app_commands.Choice(name='素材', value='material'),
        app_commands.Choice(name='モンスター', value='mob'),
        app_commands.Choice(name='採集', value='gathering'),
        app_commands.Choice(name='NPC', value='npc')
    ])
    async def upload_csv(self, interaction: discord.Interaction, csv_type: str, csv_file: discord.Attachment):
        """CSV ファイルをアップロード"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        if not csv_file.filename.endswith('.csv'):
            await interaction.response.send_message("CSVファイルを選択してください", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # バックアップを作成
            if self.bot.config['features']['auto_backup']:
                backup_file = await self.bot.db_manager.backup_database(
                    self.bot.config['database']['backup_path']
                )
                logger.info(f"バックアップを作成: {backup_file}")
            
            # CSVを処理
            result = await self.bot.csv_manager.process_csv_upload(
                csv_file, csv_type
            )
            
            if result['success']:
                await interaction.followup.send(f"✅ {csv_type}データの更新が完了しました\n"
                              f"処理件数: {result['processed']}")
            else:
                await interaction.followup.send(f"❌ CSVの処理に失敗しました: {result['error']}")
                
        except Exception as e:
            logger.error(f"CSV アップロードエラー: {e}")
            await interaction.followup.send("CSV処理中にエラーが発生しました")
    
    @app_commands.command(name='stats', description='検索統計やシステム情報を表示')
    @app_commands.describe(stat_type='表示する統計の種類')
    @app_commands.choices(stat_type=[
        app_commands.Choice(name='検索ランキング', value='search_ranking')
    ])
    async def show_stats(self, interaction: discord.Interaction, stat_type: str = 'search_ranking'):
        """統計情報を表示"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            if stat_type == 'search_ranking':
                ranking = await self.bot.db_manager.get_search_ranking(10)
                embed = await self.bot.embed_manager.create_stats_embed(ranking, 'search_ranking')
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"統計表示エラー: {e}")
            await interaction.followup.send("統計表示中にエラーが発生しました")
    
    @app_commands.command(name='add_admin_role', description='管理者ロールを追加')
    @app_commands.describe(role='追加する管理者ロール')
    async def add_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        """管理者ロールを追加"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        try:
            # 現在の管理者ロールリストを取得
            admin_roles = self.bot.config['permissions']['admin_roles']
            
            # 既に登録されているかチェック
            if role.id in admin_roles:
                await interaction.response.send_message(f"❌ ロール **{role.name}** は既に管理者ロールとして登録されています", ephemeral=True)
                return
            
            # ロールを追加
            admin_roles.append(role.id)
            self.bot.config['permissions']['admin_roles'] = admin_roles
            
            # 設定ファイルを更新
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, ensure_ascii=False, indent=2)
            
            # 環境変数も更新（必要な場合）
            if os.getenv('ADMIN_ROLE_IDS'):
                current_roles = os.getenv('ADMIN_ROLE_IDS').split(',')
                if str(role.id) not in current_roles:
                    current_roles.append(str(role.id))
                    os.environ['ADMIN_ROLE_IDS'] = ','.join(current_roles)
            
            await interaction.response.send_message(f"✅ ロール **{role.name}** を管理者ロールに追加しました", ephemeral=True)
            
            # ログチャンネルに通知
            if self.bot.config['permissions']['log_channel_id']:
                log_channel = self.bot.get_channel(self.bot.config['permissions']['log_channel_id'])
                if log_channel:
                    embed = discord.Embed(
                        title="管理者ロール追加",
                        description=f"{interaction.user.mention} が **{role.name}** を管理者ロールに追加しました",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    await log_channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"管理者ロール追加エラー: {e}")
            await interaction.response.send_message("❌ 管理者ロールの追加中にエラーが発生しました", ephemeral=True)
    
    @app_commands.command(name='add_allowed_channel', description='BOTが利用可能なチャンネルを追加')
    @app_commands.describe(channel='追加するチャンネル')
    async def add_allowed_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """利用可能チャンネルを追加"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        try:
            # 現在の許可チャンネルリストを取得
            allowed_channels = self.bot.config['permissions']['allowed_channels']
            
            # 既に登録されているかチェック
            if channel.id in allowed_channels:
                await interaction.response.send_message(f"❌ チャンネル **{channel.name}** は既に利用可能チャンネルとして登録されています", ephemeral=True)
                return
            
            # チャンネルを追加
            allowed_channels.append(channel.id)
            self.bot.config['permissions']['allowed_channels'] = allowed_channels
            
            # 設定ファイルを更新
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, ensure_ascii=False, indent=2)
            
            await interaction.response.send_message(f"✅ チャンネル **{channel.name}** をBOT利用可能チャンネルに追加しました", ephemeral=True)
            
            # ログチャンネルに通知
            if self.bot.config['permissions']['log_channel_id']:
                log_channel = self.bot.get_channel(self.bot.config['permissions']['log_channel_id'])
                if log_channel:
                    embed = discord.Embed(
                        title="利用可能チャンネル追加",
                        description=f"{interaction.user.mention} が {channel.mention} を利用可能チャンネルに追加しました",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    await log_channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"利用可能チャンネル追加エラー: {e}")
            await interaction.response.send_message("❌ 利用可能チャンネルの追加中にエラーが発生しました", ephemeral=True)
    
    @app_commands.command(name='remove_admin_role', description='管理者ロールを削除')
    @app_commands.describe(role='削除する管理者ロール')
    async def remove_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        """管理者ロールを削除"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        try:
            # 現在の管理者ロールリストを取得
            admin_roles = self.bot.config['permissions']['admin_roles']
            
            # 登録されているかチェック
            if role.id not in admin_roles:
                await interaction.response.send_message(f"❌ ロール **{role.name}** は管理者ロールとして登録されていません", ephemeral=True)
                return
            
            # ロールを削除
            admin_roles.remove(role.id)
            self.bot.config['permissions']['admin_roles'] = admin_roles
            
            # 設定ファイルを更新
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, ensure_ascii=False, indent=2)
            
            await interaction.response.send_message(f"✅ ロール **{role.name}** を管理者ロールから削除しました", ephemeral=True)
            
            # ログチャンネルに通知
            if self.bot.config['permissions']['log_channel_id']:
                log_channel = self.bot.get_channel(self.bot.config['permissions']['log_channel_id'])
                if log_channel:
                    embed = discord.Embed(
                        title="管理者ロール削除",
                        description=f"{interaction.user.mention} が **{role.name}** を管理者ロールから削除しました",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    await log_channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"管理者ロール削除エラー: {e}")
            await interaction.response.send_message("❌ 管理者ロールの削除中にエラーが発生しました", ephemeral=True)
    
    @app_commands.command(name='remove_allowed_channel', description='BOT利用可能チャンネルを削除')
    @app_commands.describe(channel='削除するチャンネル')
    async def remove_allowed_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """利用可能チャンネルを削除"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        try:
            # 現在の許可チャンネルリストを取得
            allowed_channels = self.bot.config['permissions']['allowed_channels']
            
            # 登録されているかチェック
            if channel.id not in allowed_channels:
                await interaction.response.send_message(f"❌ チャンネル **{channel.name}** は利用可能チャンネルとして登録されていません", ephemeral=True)
                return
            
            # チャンネルを削除
            allowed_channels.remove(channel.id)
            self.bot.config['permissions']['allowed_channels'] = allowed_channels
            
            # 設定ファイルを更新
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, ensure_ascii=False, indent=2)
            
            await interaction.response.send_message(f"✅ チャンネル **{channel.name}** をBOT利用可能チャンネルから削除しました", ephemeral=True)
            
            # ログチャンネルに通知
            if self.bot.config['permissions']['log_channel_id']:
                log_channel = self.bot.get_channel(self.bot.config['permissions']['log_channel_id'])
                if log_channel:
                    embed = discord.Embed(
                        title="利用可能チャンネル削除",
                        description=f"{interaction.user.mention} が {channel.mention} を利用可能チャンネルから削除しました",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    await log_channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"利用可能チャンネル削除エラー: {e}")
            await interaction.response.send_message("❌ 利用可能チャンネルの削除中にエラーが発生しました", ephemeral=True)
    
    @app_commands.command(name='list_permissions', description='現在の権限設定を表示')
    async def list_permissions(self, interaction: discord.Interaction):
        """現在の権限設定を表示"""
        if not self.bot.is_admin_interaction(interaction):
            await interaction.response.send_message("このコマンドは管理者のみ実行可能です", ephemeral=True)
            return
        
        try:
            embed = discord.Embed(
                title="権限設定一覧",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # 管理者ロール
            admin_roles = self.bot.config['permissions']['admin_roles']
            if admin_roles:
                role_mentions = []
                for role_id in admin_roles:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        role_mentions.append(role.mention)
                    else:
                        role_mentions.append(f"削除されたロール (ID: {role_id})")
                embed.add_field(
                    name="管理者ロール",
                    value="\n".join(role_mentions),
                    inline=False
                )
            else:
                embed.add_field(
                    name="管理者ロール",
                    value="設定なし",
                    inline=False
                )
            
            # 利用可能チャンネル
            allowed_channels = self.bot.config['permissions']['allowed_channels']
            if allowed_channels:
                channel_mentions = []
                for channel_id in allowed_channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        channel_mentions.append(channel.mention)
                    else:
                        channel_mentions.append(f"削除されたチャンネル (ID: {channel_id})")
                embed.add_field(
                    name="BOT利用可能チャンネル",
                    value="\n".join(channel_mentions),
                    inline=False
                )
            else:
                embed.add_field(
                    name="BOT利用可能チャンネル",
                    value="設定なし（BOTは動作しません）",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"権限設定表示エラー: {e}")
            await interaction.response.send_message("❌ 権限設定の表示中にエラーが発生しました", ephemeral=True)
    
    @commands.command(name='upload_csv')
    async def upload_csv_command(self, ctx, csv_type: str = None):
        """CSVファイルをアップロード（通常コマンド版）"""
        # 管理者権限チェック
        user_roles = [role.id for role in ctx.author.roles] if ctx.author.roles else []
        if not self.bot.is_admin(ctx.author.id, user_roles):
            await ctx.reply("このコマンドは管理者のみ実行可能です")
            return
        
        # csv_typeの検証
        valid_types = ['equipment', 'material', 'mob', 'gathering', 'npc']
        if not csv_type or csv_type not in valid_types:
            await ctx.reply(f"CSVタイプを指定してください: {', '.join(valid_types)}")
            return
        
        # 添付ファイルチェック
        if not ctx.message.attachments:
            await ctx.reply("CSVファイルを添付してください")
            return
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            await ctx.reply("CSVファイルを選択してください")
            return
        
        # 処理中メッセージ
        processing_msg = await ctx.reply("CSVファイルを処理中...")
        
        try:
            # バックアップを作成
            if self.bot.config['features']['auto_backup']:
                backup_file = await self.bot.db_manager.backup_database(
                    self.bot.config['database']['backup_path']
                )
                logger.info(f"バックアップを作成: {backup_file}")
            
            # CSVを処理
            result = await self.bot.csv_manager.process_csv_upload(attachment, csv_type)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ CSV アップロード成功",
                    description=result['message'],
                    color=discord.Color.green()
                )
                embed.add_field(name="処理件数", value=f"{result['processed']}件", inline=True)
                embed.add_field(name="タイプ", value=csv_type, inline=True)
                await processing_msg.edit(content=None, embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ CSV アップロード失敗",
                    description=result['error'],
                    color=discord.Color.red()
                )
                if 'errors' in result:
                    embed.add_field(
                        name="エラー詳細",
                        value="\n".join(result['errors'][:5]),
                        inline=False
                    )
                await processing_msg.edit(content=None, embed=embed)
                
        except Exception as e:
            logger.error(f"CSVアップロードエラー: {e}")
            await processing_msg.edit(content="CSVアップロード中にエラーが発生しました")

# グローバル変数でbotインスタンスとシャットダウンイベントを保持
bot_instance = None
shutdown_event = None

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    print("\nシャットダウンシグナルを受信しました...")
    if shutdown_event:
        shutdown_event.set()

async def shutdown_bot():
    """適切なBotシャットダウン処理"""
    global bot_instance
    if bot_instance and not bot_instance.is_closed():
        logger.info("Botをシャットダウンしています...")
        await bot_instance.close()
        logger.info("Botが正常に終了しました")



async def main():
    """メイン実行関数"""
    global bot_instance, shutdown_event
    
    # シャットダウンイベントを作成
    shutdown_event = asyncio.Event()
    
    # シグナルハンドラーを登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # ログディレクトリを作成
    os.makedirs('./logs', exist_ok=True)
    
    bot_instance = ItemReferenceBot()
    
    # Cogを追加
    await bot_instance.add_cog(ItemCommands(bot_instance))
    await bot_instance.add_cog(AdminCommands(bot_instance))
    
    try:
        # Botを起動
        token = bot_instance.config['bot']['token']
        if token == "環境変数から取得":
            logger.error("DISCORD_TOKEN環境変数が設定されていません")
            return
        
        logger.info("Botを起動しています... (Ctrl+Cで停止)")
        
        # Botの起動とシャットダウンイベントを並行実行
        bot_task = asyncio.create_task(bot_instance.start(token))
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        # どちらかが先に完了するまで待機
        done, pending = await asyncio.wait(
            [bot_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # シャットダウンイベントが先に完了した場合
        if shutdown_task in done:
            logger.info("シャットダウンシグナルを受信しました")
            
            # Botタスクをキャンセル
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
    except Exception as e:
        logger.error(f"Bot実行エラー: {e}")
    finally:
        await shutdown_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # ここではKeyboardInterruptをキャッチしてサイレントに終了
        pass