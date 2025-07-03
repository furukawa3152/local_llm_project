import shutil
import os
import subprocess
import re
def fetch_and_print_text_file_by_id(file_id: int):
    # フォルダはIDの下一桁
    folder_name = str(file_id % 10)
    file_name = f"{file_id}.txt"
    source_path = f"/Volumes/shoken-2/{folder_name}/{file_name}"
    #\\172.16.10.180\d\Users\rsn\public_html\shokenフォルダを、/Volumes/shoken-1としてマウント済み
    # 作業ディレクトリと一時保存先のパス
    current_dir = os.getcwd()
    temp_dir = os.path.join(current_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    destination_path = os.path.join(temp_dir, "target_file.txt")

    try:
        # ファイルをコピー
        shutil.copy(source_path, destination_path)
        print(f"[コピー成功] {destination_path}")

        # ファイルの中身を読み込み＆表示
        with open(destination_path, 'r', encoding='cp932') as f:
            content = f.read()
            print("[ファイル内容]")
            return(content)

    except Exception as e:
        print(f"[エラー] ファイルの取得または読み込みに失敗しました: {e}")
    finally:
        # コピー先のファイルを削除
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
                print(f"[クリーンアップ完了] 一時ファイル削除: {destination_path}")
            except Exception as e:
                print(f"[クリーンアップ失敗] 一時ファイル削除できませんでした: {e}")

def extract_ascending_soap_text(text, max_chars=2500):
    if len(text) <= max_chars:
        return text  # 並び替えもせずにそのまま返す
    else:
        # ●24/06/17 のような見出しとその内容をワンセットで分割
        pattern = r"(●\d{2}/\d{2}/\d{2} .+?)(?=(●\d{2}/\d{2}/\d{2}|\Z))"
        records = re.findall(pattern, text, flags=re.DOTALL)
        records = [rec[0] for rec in records]

        # 昇順（古い順）に並べ替え
        records.reverse()

        # 後ろから詰めて、3000文字分を抽出
        extracted = []
        total_length = 0

        for record in reversed(records):
            record_length = len(record)
            if total_length + record_length > max_chars:
                break
            extracted.insert(0, record)
            total_length += record_length

        return "\n\n".join(extracted)

def mount_if_not_mounted(server_url: str, mount_point: str):
    # マウント済みかを確認
    def is_mounted(path):
        result = subprocess.run(["mount"], capture_output=True, text=True)
        return path in result.stdout

    # すでにマウントされていたら終了
    if is_mounted(mount_point):
        print(f"{mount_point} はすでにマウントされています。処理を終了します。")
        return

    # マウントポイントが残っていたら削除（不完全なマウント対策）
    if os.path.exists(mount_point):
        try:
            os.rmdir(mount_point)
        except OSError as e:
            print(f"{mount_point} を削除できませんでした: {e}")
            return

    # マウントポイント作成
    os.makedirs(mount_point)

    # マウント処理
    try:
        subprocess.run(["mount_smbfs", server_url, mount_point], check=True)
        print("マウント成功")
    except subprocess.CalledProcessError as e:
        print("マウントに失敗しました:", e)

if __name__ == '__main__':

    # 使用例
    print(fetch_and_print_text_file_by_id(130720))
    #server_url = "//:guest@172.16.10.180/d/Users/rsn/public_html/shoken"
    #mount_point = "/Volumes/shoken-1"

    #mount_if_not_mounted(server_url, mount_point)





