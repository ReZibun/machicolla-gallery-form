import streamlit as st
import datetime
import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

# =====================
# 🔧 設定
# =====================
DEBUG = False  # ← 本番では False に切り替え

# 環境変数を読み込む
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase クライアント作成
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# タイトル
st.title("アートギャラリー投稿フォーム")
st.write("以下の項目に入力してください。")

# =====================
# 📋 入力フォーム
# =====================
with st.form(key='upload_form'):

    artist_name = st.text_input("### アーティスト名（必須）")
    title = st.text_input("作品名（テーマ）（必須）")
    description = st.text_area("作品に込めた想い（必須）", height=100)
    additional_message = st.text_area("何か伝えたいことがあればこちらに！（任意）", height=100)

    st.markdown("#### 制作年月日")
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.selectbox("年", list(range(2024, datetime.date.today().year + 1)),
                            index=len(list(range(2024, datetime.date.today().year + 1))) - 1)
    with col2:
        month = st.selectbox("月", list(range(1, 13)), index=datetime.date.today().month - 1)
    with col3:
        day = st.selectbox("日", list(range(1, 32)), index=datetime.date.today().day - 1)

    production_date = datetime.date(year, month, day)
    image_file = st.file_uploader("作品画像をアップロード（必須）", type=["jpg", "jpeg", "png"])
    submit_button = st.form_submit_button(label='送信')

# =====================
# 🚀 送信後の処理
# =====================
    if submit_button:
        if not artist_name or not title or not description or not image_file:
            st.error("❌ 必須項目をすべて入力・選択してください。")
        else:
            try:
                # 🔽 ファイル読み込みと保存パス設定
                file_bytes = image_file.read()
                file_name = image_file.name
                unique_filename = f"{uuid.uuid4()}_{file_name}"
                file_path = f"artworks/{unique_filename}"

                # 🔽 Supabase Storage へアップロード
                upload_response = supabase.storage.from_("artworks").upload(
                    file_path, file_bytes, {"content-type": image_file.type}
                )

                # 🔽 INSERT用データ整形
                data = {
                    "artist_name": artist_name,
                    "title": title,
                    "description": description,
                    "additional_message": additional_message,
                    "production_date": production_date.isoformat(),
                    "image_path": file_path,
                    "is_approved": False
                }

                # 🔽 Supabase テーブルへ INSERT 実行
                response = supabase.table("artworks").insert(data).execute()

                # ✅ 成功判定
                if response.data and len(response.data) > 0:
                    st.success("✅ 投稿が完了しました！ 審査後に掲載されます。ありがとうございました。")
                else:
                    st.error("❌ 投稿に失敗しました。INSERTは実行されたがデータが返されませんでした。")

                # ✅ デバッグ出力（切替可能）
                if DEBUG:
                    st.write("🟡 ストレージアップロード結果：", upload_response)
                    st.write("🟡 アップロード直前のデータ内容：", data)
                    st.write("🟢 SupabaseのINSERTレスポンス：", response)

            except Exception as e:
                st.error(f"⚠️ エラーが発生しました：{str(e)}")
                if DEBUG:
                    st.exception(e)  # 詳細トレースバック出力（DEBUG時のみ）