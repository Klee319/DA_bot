#!/usr/bin/env python3
"""
装備（モブ討伐）のボタンラベルテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import AcquisitionDetailsButton

def test_mob_equipment_button():
    """装備（モブ討伐）のボタンラベルテスト"""
    print("🔘 装備（モブ討伐）ボタンラベルテスト開始...")
    
    # 装備用ボタン（モブ討伐）
    print(f"📱 装備用ボタン（モブ討伐）:")
    equipment_mob_button = AcquisitionDetailsButton('equipments', 'モブ討伐')
    print(f"  AcquisitionDetailsButton: {equipment_mob_button.label}")
    
    # 装備用ボタン（鍛冶）
    print(f"📱 装備用ボタン（鍛冶）:")
    equipment_craft_button = AcquisitionDetailsButton('equipments', '鍛冶')
    print(f"  AcquisitionDetailsButton: {equipment_craft_button.label}")
    
    print("\n✅ 装備（モブ討伐）ボタンラベルテスト完了!")

if __name__ == "__main__":
    test_mob_equipment_button()