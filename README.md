README.md
# YouTube Audio Extractor

FastAPIベースのYouTube動画から音声を抽出するAPIサービス。

https://claude.ai/chat/c67c13ff-9ca7-4f8d-aad6-466c1adc1dc5

## 使用方法
このコンテナは、バックエンドで使用することができます。ポート7783に対して、以下のようなRESTアクセスを行うことで使用できます。UIは適当に作成してください。基本的にはアドオンとして使用すると便利です。

```bash
curl -X 'POST' \
  'http://localhost:7783/api/v1/extract-audio' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "url": "https://www.youtube.com/watch?v=rBL930dHVkY"
}'
```


## 機能
- YouTube URLから音声(MP3)を抽出
- 320kbps高品質音声出力
- 非同期処理対応

## 開発環境のセットアップ
1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/youtube_audio_extractor.git
cd youtube_audio_extractors
```

## APIアクセス
- Swagger UI: http://localhost:7783/docs
- ReDoc: http://localhost:7783/redoc