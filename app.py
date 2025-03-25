import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からLINEのシークレット情報を取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境変数 LINE_CHANNEL_SECRET または LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")

# LINE APIのセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 気象庁APIのエンドポイント
JMA_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json"  # 東京の例

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # X-Line-Signatureヘッダーの取得
    signature = request.headers.get("X-Line-Signature")

    # リクエストのボディ取得
    body = request.get_data(as_text=True)
    print("Received Signature:", signature)
    print("Received Body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

def get_weather(city_name):
    """指定された地域の天気情報を取得"""
    try:
        # 気象庁APIデータを取得
        response = requests.get(JMA_API_URL)
        if response.status_code == 200:
            data = response.json()
            # データ解析（ここでは東京を想定）
            weather_info = data[0]['timeSeries'][0]['areas'][0]  # 東京エリアのデータ
            description = weather_info['weathers'][0]  # 天気情報
            return f"{city_name}の天気: {description}"
        else:
            return "天気情報を取得できませんでした。"
    except Exception as e:
        print(f"エラー: {e}")
        return "天気情報の取得中にエラーが発生しました。"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ ユーザーからのメッセージを天気情報に変換して返信 """
    user_message = event.message.text.strip()  # ユーザーからのメッセージ
    if "天気" in user_message:
        # 地域名を取得（例: "東京の天気" -> "東京"）
        city_name = user_message.replace("の天気", "").strip()
        reply_message = get_weather(city_name)
    else:
        reply_message = "「〇〇の天気」と入力してください（例: 東京の天気）"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
