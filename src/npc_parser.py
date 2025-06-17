"""
NPC交換データのパース処理
複数交換パターンに対応
"""
import re
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class NPCExchangeParser:
    """NPC交換データのパーサー"""
    
    @staticmethod
    def parse_exchange_items(obtainable_items: str, required_materials: str, 
                           exp_str: str = None, gold_str: str = None) -> List[Dict[str, Any]]:
        """
        NPC交換データをパースして個別の交換パターンに分解
        
        Args:
            obtainable_items: 入手アイテム（カンマ区切り）
            required_materials: 必要素材/価格（カンマ区切り）
            exp_str: EXP（カンマ区切りまたはEXPプレフィックス付き）
            gold_str: GOLD（カンマ区切り）
            
        Returns:
            交換パターンのリスト
        """
        exchanges = []
        
        try:
            # 各フィールドをパース
            obtainable_list = NPCExchangeParser._parse_item_list(obtainable_items)
            required_list = NPCExchangeParser._parse_required_materials(required_materials)
            exp_list = NPCExchangeParser._parse_exp_values(exp_str)
            gold_list = NPCExchangeParser._parse_numeric_values(gold_str)
            
            # 最大長を取得
            max_length = max(
                len(obtainable_list),
                len(required_list) if required_list else 0
            )
            
            # 各インデックスで交換パターンを作成
            for i in range(max_length):
                exchange = {
                    'obtainable_item': obtainable_list[i] if i < len(obtainable_list) else None,
                    'required_materials': required_list[i] if required_list and i < len(required_list) else None,
                    'exp': exp_list[i] if exp_list and i < len(exp_list) else None,
                    'gold': gold_list[i] if gold_list and i < len(gold_list) else None,
                    'index': i
                }
                exchanges.append(exchange)
                
        except Exception as e:
            logger.error(f"NPC交換データパースエラー: {e}")
            # エラー時は単一の交換パターンとして扱う
            exchanges.append({
                'obtainable_item': obtainable_items,
                'required_materials': required_materials,
                'exp': exp_str,
                'gold': gold_str,
                'index': 0
            })
            
        return exchanges
    
    @staticmethod
    def _parse_item_list(items_str: str) -> List[str]:
        """アイテムリストをパース（カンマ区切り）"""
        if not items_str:
            return []
            
        # カンマで分割してトリム
        items = [item.strip() for item in str(items_str).split(',') if item.strip()]
        return items
    
    @staticmethod
    def _parse_required_materials(materials_str: str) -> List[str]:
        """必要素材をパース（複数素材の連続記述に対応）"""
        if not materials_str:
            return []
            
        materials = []
        current_materials = []
        
        # カンマで分割
        parts = str(materials_str).split(',')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 価格表記（数字+G）の場合は単独の要素として扱う
            if re.match(r'^\d+G$', part):
                materials.append(part)
            else:
                # アイテム:数量 の形式を検出
                item_pattern = r'([^:]+):(\d+)'
                matches = re.findall(item_pattern, part)
                
                if matches:
                    # 複数のアイテム:数量が連続している場合
                    material_list = []
                    for item_name, quantity in matches:
                        material_list.append(f"{item_name.strip()}:{quantity}")
                    materials.append(' + '.join(material_list))
                else:
                    # パターンにマッチしない場合はそのまま
                    materials.append(part)
                    
        return materials
    
    @staticmethod
    def _parse_exp_values(exp_str: str) -> List[int]:
        """EXP値をパース（EXPプレフィックス対応）"""
        if not exp_str:
            return []
            
        exp_values = []
        exp_str = str(exp_str).strip()
        
        # EXPプレフィックスを除去
        if exp_str.startswith('EXP'):
            exp_str = exp_str[3:]
        
        # カンマで分割して数値に変換
        for value in exp_str.split(','):
            value = value.strip()
            if value:
                try:
                    exp_values.append(int(value))
                except ValueError:
                    logger.warning(f"EXP値の変換エラー: {value}")
                    exp_values.append(0)
                    
        return exp_values
    
    @staticmethod
    def _parse_numeric_values(values_str: str) -> List[int]:
        """数値リストをパース（カンマ区切り、G付き値対応）"""
        if not values_str:
            return []
            
        numeric_values = []
        
        for value in str(values_str).split(','):
            value = value.strip()
            if value:
                try:
                    # G付きの値（例: 1380G）を処理
                    if value.endswith('G'):
                        value = value[:-1]
                    numeric_values.append(int(value))
                except ValueError:
                    logger.warning(f"数値変換エラー: {value}")
                    numeric_values.append(0)
                    
        return numeric_values
    
    @staticmethod
    def format_exchange_display(exchange: Dict[str, Any], business_type: str) -> str:
        """交換パターンを表示用にフォーマット"""
        obtainable = exchange.get('obtainable_item', '不明')
        required = exchange.get('required_materials', '')
        
        if business_type == '購入':
            return f"{obtainable} → {required}"
        elif business_type == '交換':
            return f"{obtainable} ← {required}"
        else:
            return obtainable