import pandas as pd
import aiosqlite
import asyncio
import logging
import io
import aiohttp
from typing import Dict, Any, List, Optional
import jaconv
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVManager:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.csv_mapping = config['csv_mapping']
    
    async def process_csv_upload(self, attachment, csv_type: str) -> Dict[str, Any]:
        """CSVファイルをアップロードして処理"""
        try:
            # ファイルをダウンロード
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status != 200:
                        return {"success": False, "error": "ファイルのダウンロードに失敗"}
                    
                    content = await response.read()
            
            # CSVを読み込み（2行目をスキップ：1行目=ヘッダー、2行目=説明、3行目以降=データ）
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8', skiprows=[1])
            
            # バリデーション
            validation_result = await self.validate_csv(df, csv_type)
            if not validation_result['valid']:
                return {"success": False, "error": validation_result['errors']}
            
            # データを正規化
            normalized_df = await self.normalize_csv_data(df, csv_type)
            
            # データベースに挿入
            processed_count = await self.insert_csv_data(normalized_df, csv_type)
            
            logger.info(f"{csv_type}データを{processed_count}件処理しました")
            
            return {
                "success": True, 
                "processed": processed_count,
                "message": f"{csv_type}データの更新が完了"
            }
            
        except Exception as e:
            logger.error(f"CSV処理エラー: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_csv(self, df: pd.DataFrame, csv_type: str) -> Dict[str, Any]:
        """CSVデータのバリデーション"""
        errors = []
        
        try:
            # 必須カラムの確認
            required_columns = self._get_required_columns(csv_type)
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                errors.append(f"必須カラムが不足: {missing_columns}")
            
            # 正式名称の重複チェック（mobの場合は同名でもレベル違いは許可）
            if '正式名称' in df.columns:
                if csv_type == 'mob':
                    # mobの場合は正式名称+必要レベルの組み合わせで重複チェック
                    if '必要レベル' in df.columns:
                        duplicate_combinations = df[df[['正式名称', '必要レベル']].duplicated()]
                        if not duplicate_combinations.empty:
                            duplicate_list = []
                            for _, row in duplicate_combinations.iterrows():
                                duplicate_list.append(f"{row['正式名称']}(Lv.{row['必要レベル']})")
                            errors.append(f"正式名称+レベルの重複: {duplicate_list}")
                    else:
                        # 必要レベルカラムがない場合は従来通り
                        duplicates = df[df['正式名称'].duplicated()]
                        if not duplicates.empty:
                            duplicate_names = duplicates['正式名称'].tolist()
                            errors.append(f"正式名称の重複: {duplicate_names}")
                else:
                    # mob以外の場合は従来通り正式名称で重複チェック
                    duplicates = df[df['正式名称'].duplicated()]
                    if not duplicates.empty:
                        duplicate_names = duplicates['正式名称'].tolist()
                        errors.append(f"正式名称の重複: {duplicate_names}")
            
            # 正式名称の空値チェック
            if '正式名称' in df.columns:
                null_names = df[df['正式名称'].isnull() | (df['正式名称'] == '')]
                if not null_names.empty:
                    errors.append(f"正式名称が空の行: {len(null_names)}件")
            
            # データ型の検証
            validation_errors = await self._validate_data_types(df, csv_type)
            errors.extend(validation_errors)
            
            return {"valid": len(errors) == 0, "errors": errors}
            
        except Exception as e:
            return {"valid": False, "errors": [f"バリデーションエラー: {str(e)}"]}
    
    def _get_required_columns(self, csv_type: str) -> List[str]:
        """CSVタイプに応じた必須カラムを取得"""
        required_columns = {
            'equipment': ['正式名称'],
            'material': ['正式名称'],
            'mob': ['正式名称'],
            'gathering': ['収集場所', '収集方法'],
            'npc': ['配置場所', '名前']
        }
        return required_columns.get(csv_type, [])
    
    async def _validate_data_types(self, df: pd.DataFrame, csv_type: str) -> List[str]:
        """データ型の検証"""
        errors = []
        
        try:
            # NPCタイプの場合は特別な処理
            if csv_type == 'npc':
                # NPCのEXP/GOLDは複数値のカンマ区切りやEXPプレフィックス付きを許可
                return []
            
            # 数値カラムの検証（~記号を含む値も許可）
            numeric_columns = ['必要レベル', 'EXP', 'Gold', '必要守備力']
            for col in numeric_columns:
                if col in df.columns:
                    # 数値に変換できない値をチェック（~記号を含む値は許可）
                    non_numeric = df[col].dropna()
                    if len(non_numeric) > 0:
                        invalid_values = []
                        for value in non_numeric:
                            str_value = str(value).strip()
                            if str_value:  # 空でない場合のみチェック
                                # ~記号を含む値（例: "3~4", "5~6"）やカンマ区切り（例: "15,20"）は許可
                                if '~' in str_value:
                                    # ~で区切られた値が数値かチェック
                                    parts = str_value.split('~')
                                    valid_range = True
                                    for part in parts:
                                        try:
                                            float(part.strip())
                                        except ValueError:
                                            valid_range = False
                                            break
                                    if not valid_range:
                                        invalid_values.append(str_value)
                                elif ',' in str_value:
                                    # カンマ区切りの値が数値かチェック
                                    parts = str_value.split(',')
                                    valid_list = True
                                    for part in parts:
                                        try:
                                            float(part.strip())
                                        except ValueError:
                                            valid_list = False
                                            break
                                    if not valid_list:
                                        invalid_values.append(str_value)
                                else:
                                    # 通常の数値チェック
                                    try:
                                        float(str_value)
                                    except ValueError:
                                        invalid_values.append(str_value)
                        
                        if invalid_values:
                            errors.append(f"{col}カラムに無効な値が含まれています: {invalid_values}")
            
            return errors
            
        except Exception as e:
            return [f"データ型検証エラー: {str(e)}"]
    
    async def normalize_csv_data(self, df: pd.DataFrame, csv_type: str) -> pd.DataFrame:
        """CSVデータの正規化"""
        try:
            # カラム名をマッピング
            mapping = self.csv_mapping[csv_type]
            df_renamed = df.rename(columns=mapping)
            
            # 日本語テキストの正規化
            text_columns = ['formal_name', 'common_name', 'description', 'name', 'location']
            for col in text_columns:
                if col in df_renamed.columns:
                    df_renamed[col] = df_renamed[col].astype(str).apply(self._normalize_japanese_text)
            
            # NULL値の処理
            df_renamed = df_renamed.where(pd.notnull(df_renamed), None)
            
            # NPCタイプの場合は特別な処理
            if csv_type == 'npc':
                # NPCのEXP/GOLDカラムの処理
                npc_special_columns = ['exp', 'gold']
                for col in npc_special_columns:
                    if col in df_renamed.columns:
                        processed_values = []
                        for value in df_renamed[col].values:
                            if pd.isna(value) or value == '' or str(value).strip() == '' or str(value) == 'nan':
                                processed_values.append(None)
                            else:
                                # そのまま文字列として保持（EXPプレフィックスやカンマ区切りを保持）
                                processed_values.append(str(value).strip())
                        df_renamed[col] = processed_values
            else:
                # 数値カラムの処理（純粋な数値はint、~やカンマ含む値はそのまま文字列で保持）
                numeric_columns = ['required_level', 'exp', 'gold', 'required_defense']
                for col in numeric_columns:
                    if col in df_renamed.columns:
                        # 各値を個別に処理（NULL値も考慮）
                        processed_values = []
                        original_values = df_renamed[col].values
                        
                        for value in original_values:
                            # pd.isna()とNaNの判定を追加
                            if pd.isna(value) or value == '' or str(value).strip() == '' or str(value) == 'nan':
                                processed_values.append(None)
                            else:
                                str_value = str(value).strip()
                                # ~やカンマが含まれていない純粋な数値の場合はintに変換
                                if '~' not in str_value and ',' not in str_value:
                                    try:
                                        # 小数点を含む場合は四捨五入してintに
                                        processed_values.append(int(float(str_value)))
                                    except ValueError:
                                        # 変換できない場合はそのまま文字列
                                        processed_values.append(str_value)
                                else:
                                    # ~やカンマを含む場合はそのまま文字列で保持
                                    processed_values.append(str_value)
                        
                        df_renamed[col] = processed_values
            
            # NULL値の再処理（数値処理後に実行）
            df_renamed = df_renamed.where(pd.notnull(df_renamed), None)
            
            # タイムスタンプを追加
            current_time = datetime.now()
            df_renamed['created_at'] = current_time
            df_renamed['updated_at'] = current_time
            
            return df_renamed
            
        except Exception as e:
            logger.error(f"データ正規化エラー: {e}")
            raise
    
    def _normalize_japanese_text(self, text: str) -> str:
        """日本語テキストの正規化"""
        if pd.isna(text) or text == 'nan':
            return None
        
        try:
            # 文字列に変換
            text = str(text).strip()
            
            # 空文字列の場合はNoneを返す
            if not text:
                return None
            
            # 全角→半角変換（数字とアルファベット）
            text = jaconv.z2h(text, kana=False, ascii=True, digit=True)
            
            # 半角カタカナ→全角カタカナ変換
            text = jaconv.h2z(text, kana=True, ascii=False, digit=False)
            
            return text
            
        except Exception as e:
            logger.warning(f"テキスト正規化エラー: {e}, text: {text}")
            return text
    
    async def insert_csv_data(self, df: pd.DataFrame, csv_type: str) -> int:
        """正規化されたデータをデータベースに挿入"""
        try:
            # テーブル名を決定
            table_mapping = {
                'equipment': 'equipments',
                'material': 'materials',
                'mob': 'mobs',
                'gathering': 'gatherings',
                'npc': 'npcs'
            }
            table_name = table_mapping[csv_type]
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                # 既存データを削除（完全更新）
                await db.execute(f"DELETE FROM {table_name}")
                
                # 新しいデータを挿入
                columns = df.columns.tolist()
                placeholders = ', '.join(['?' for _ in columns])
                
                sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # DataFrameを辞書のリストに変換
                data_rows = []
                for _, row in df.iterrows():
                    # SQLite用に値を適切に変換
                    converted_row = []
                    for value in row.values:
                        if pd.isna(value):
                            converted_row.append(None)
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            converted_row.append(str(value))
                        else:
                            converted_row.append(value)
                    data_rows.append(tuple(converted_row))
                
                await db.executemany(sql, data_rows)
                await db.commit()
                
                return len(data_rows)
                
        except Exception as e:
            logger.error(f"データ挿入エラー: {e}")
            raise
    
    async def export_csv(self, csv_type: str, output_path: str) -> bool:
        """データベースからCSVにエクスポート"""
        try:
            table_mapping = {
                'equipment': 'equipments',
                'material': 'materials',
                'mob': 'mobs',
                'gathering': 'gatherings',
                'npc': 'npcs'
            }
            table_name = table_mapping[csv_type]
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(f"SELECT * FROM {table_name}")
                rows = await cursor.fetchall()
                
                if not rows:
                    return False
                
                # DataFrameに変換
                df = pd.DataFrame([dict(row) for row in rows])
                
                # カラム名を元に戻す
                reverse_mapping = {v: k for k, v in self.csv_mapping[csv_type].items()}
                df_renamed = df.rename(columns=reverse_mapping)
                
                # 不要なカラムを削除
                columns_to_drop = ['id', 'created_at', 'updated_at']
                df_renamed = df_renamed.drop(columns=[col for col in columns_to_drop if col in df_renamed.columns])
                
                # CSVに出力
                df_renamed.to_csv(output_path, index=False, encoding='utf-8')
                
                logger.info(f"{csv_type}データを{output_path}にエクスポートしました")
                return True
                
        except Exception as e:
            logger.error(f"CSVエクスポートエラー: {e}")
            return False
    
    async def validate_existing_data(self, csv_type: str) -> Dict[str, Any]:
        """既存データの整合性チェック"""
        try:
            table_mapping = {
                'equipment': 'equipments',
                'material': 'materials',
                'mob': 'mobs',
                'gathering': 'gatherings',
                'npc': 'npcs'
            }
            table_name = table_mapping[csv_type]
            
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # 重複チェック
                cursor = await db.execute(f"""
                    SELECT formal_name, COUNT(*) as count 
                    FROM {table_name} 
                    GROUP BY formal_name 
                    HAVING COUNT(*) > 1
                """)
                duplicates = await cursor.fetchall()
                
                # NULL値チェック
                cursor = await db.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM {table_name} 
                    WHERE formal_name IS NULL OR formal_name = ''
                """)
                null_count = await cursor.fetchone()
                
                # 総件数
                cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                total_count = await cursor.fetchone()
                
                return {
                    "table": table_name,
                    "total_records": total_count['count'],
                    "duplicates": [dict(row) for row in duplicates],
                    "null_formal_names": null_count['count'],
                    "valid": len(duplicates) == 0 and null_count['count'] == 0
                }
                
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            return {"valid": False, "error": str(e)}