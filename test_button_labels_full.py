#!/usr/bin/env python3
"""
ボタンラベルの完全なテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import UsageDetailsButton, AcquisitionDetailsButton

def test_button_labels():
    """ボタンラベルのテスト"""
    print("🔘 ボタンラベルテスト開始...")
    
    # モブ用ボタン
    print(f"\n📱 モブ用ボタン:")
    mob_button = UsageDetailsButton('mobs')
    print(f"  UsageDetailsButton: {mob_button.label}")
    
    # 素材用ボタン
    print(f"\n📱 素材用ボタン:")
    material_usage_button = UsageDetailsButton('materials')
    material_acquisition_button = AcquisitionDetailsButton('materials', '')
    print(f"  UsageDetailsButton: {material_usage_button.label}")
    print(f"  AcquisitionDetailsButton: {material_acquisition_button.label}")
    
    # 装備用ボタン（鍛冶）
    print(f"\n📱 装備用ボタン（鍛冶）:")
    equipment_button = AcquisitionDetailsButton('equipments', '鍛冶')
    print(f"  AcquisitionDetailsButton: {equipment_button.label}")
    
    # 装備用ボタン（モブ討伐）
    print(f"\n⚔️ 装備用ボタン（モブ討伐）:")
    equipment_mob_button = AcquisitionDetailsButton('equipments', 'モブ討伐')
    print(f"  AcquisitionDetailsButton: {equipment_mob_button.label}")
    
    # デフォルトボタン
    print(f"\n📱 デフォルトボタン:")
    default_usage_button = UsageDetailsButton()
    default_acquisition_button = AcquisitionDetailsButton()
    print(f"  UsageDetailsButton: {default_usage_button.label}")
    print(f"  AcquisitionDetailsButton: {default_acquisition_button.label}")
    
    print("\n✅ ボタンラベルテスト完了!")

if __name__ == "__main__":
    test_button_labels()