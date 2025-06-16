#!/usr/bin/env python3
"""
ボタンラベルの簡単なテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embed_manager import UsageDetailsButton, AcquisitionDetailsButton

def test_button_labels():
    """ボタンラベルのテスト"""
    print("🔘 ボタンラベルテスト開始...")
    
    # モブ用ボタン
    print(f"📱 モブ用ボタン:")
    mob_button = UsageDetailsButton('mobs')
    print(f"  UsageDetailsButton: {mob_button.label}")
    
    # 素材用ボタン
    print(f"📱 素材用ボタン:")
    material_usage_button = UsageDetailsButton('materials')
    material_acquisition_button = AcquisitionDetailsButton('materials')
    print(f"  UsageDetailsButton: {material_usage_button.label}")
    print(f"  AcquisitionDetailsButton: {material_acquisition_button.label}")
    
    # 装備用ボタン
    print(f"📱 装備用ボタン:")
    equipment_button = AcquisitionDetailsButton('equipments')
    print(f"  AcquisitionDetailsButton: {equipment_button.label}")
    
    # デフォルトボタン
    print(f"📱 デフォルトボタン:")
    default_usage_button = UsageDetailsButton()
    default_acquisition_button = AcquisitionDetailsButton()
    print(f"  UsageDetailsButton: {default_usage_button.label}")
    print(f"  AcquisitionDetailsButton: {default_acquisition_button.label}")
    
    print("\n✅ ボタンラベルテスト完了!")

if __name__ == "__main__":
    test_button_labels()