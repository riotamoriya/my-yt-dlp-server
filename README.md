# YouTube Audio Extractor - Firefox拡張機能

## 概要
YouTube Audio Extractorは、YouTubeの動画から簡単に音声を抽出してダウンロードできるFirefox拡張機能です。

## 特徴
- YouTubeの動画から直接音声をダウンロード
- 現在再生中の動画のURLを自動入力
- シンプルで使いやすいインターフェース
- URL検証機能

## インストール方法

### 拡張機能のインストール
1. プロジェクトディレクトリを作成
```
youtube-audio-extractor/
├── manifest.json
└── content.js
```

2. `manifest.json`を作成
```json
{
  "manifest_version": 2,
  "name": "YouTube Audio Extractor",
  "version": "1.0",
  "description": "Extract audio from YouTube videos",
  "permissions": [
    "activeTab",
    "<all_urls>"
  ],
  "content_scripts": [
    {
      "matches": ["*://www.youtube.com/*"],
      "js": ["content.js"]
    }
  ]
}
```

### Firefoxへのインストール
1. Firefoxで`about:debugging`に移動
2. 「このFirefox」を選択
3. 「一時的なアドオンを読み込む」をクリック
4. プロジェクトディレクトリ内の`manifest.json`を選択

## 使用方法
1. YouTubeの動画ページを開く
2. 動画の下に表示される「音声を抽出」ボタンをクリック
3. 音声ファイルが自動的にダウンロード

## 動作要件
- バックエンドサーバーが`http://localhost:7783`で起動していること
- インターネット接続

## 注意事項
- 著作権を尊重し、個人利用の範囲内でお使いください
- ダウンロードしたコンテンツの使用は各自の責任となります

## トラブルシューティング
- バックエンドサーバーが正常に起動していることを確認
- ファイアウォールや セキュリティソフトが接続をブロックしていないか確認
- ブラウザの開発者ツールでエラーメッセージを確認

## 技術的詳細
- URL検証: 正規表現を使用
- バックエンド通信: Fetch API
- エラーハンドリング: 詳細なエラーメッセージを表示

## ライセンス
[適切なライセンスを追加]

## 免責事項
この拡張機能は教育目的で作成されています。コンテンツの違法なダウンロードは避けてください。

## サポート
問題や機能リクエストは[リポジトリのIssueページ]で報告してください。

## 開発者
[あなたの名前/ニックネーム]