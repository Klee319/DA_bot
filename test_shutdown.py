import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=== シャットダウン処理のテスト ===")
print("このテストでは、Ctrl+Cでプログラムを停止した際に")
print("適切なシャットダウンメッセージが表示されるかを確認します。")
print()
print("修正内容:")
print("1. KeyboardInterruptを適切にキャッチ")
print("2. シグナルハンドラーでクリーンなシャットダウン")
print("3. エラーメッセージではなく正常終了メッセージを表示")
print()
print("実際のBotを起動してCtrl+Cで停止してテストしてください。")
print("エラーメッセージではなく、以下のようなメッセージが表示されるはずです:")
print("- 'シャットダウンシグナルを受信しました'")
print("- 'Botをシャットダウンしています...'") 
print("- 'Botが正常に終了しました'")
print()
print("Traceback (most recent call last): のようなエラーは表示されません。")