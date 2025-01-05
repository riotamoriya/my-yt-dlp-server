function addMp3SaveButton() {
  // 既に追加されていないか確認
  const existingButton = document.getElementById('mp3-save-button');
  if (existingButton) return;

  console.log('Adding MP3 save button');

  // ボタン要素を作成
  const saveButton = document.createElement('button');
  saveButton.id = 'mp3-save-button';
  saveButton.textContent = 'MP3を保存';
  saveButton.classList.add('mp3-save-btn');

  // スタイル
  const style = document.createElement('style');
  style.textContent = `
    .mp3-save-btn {
      display: block;
      margin: 10px auto;
      padding: 10px 20px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    .mp3-save-btn:hover {
      background-color: #45a049;
    }
    .mp3-save-btn.loading {
      background-color: #ccc;
      cursor: wait;
    }
  `;

  // 動画の下にあるセクションを見つける
  const possibleContainers = [
    'div#actions.ytd-video-primary-info-renderer',
    'div#actions-inner',
    'ytd-video-primary-info-renderer #actions',
    '#top-row.ytd-video-primary-info-renderer'
  ];

  let actionSection = null;
  for (const selector of possibleContainers) {
    actionSection = document.querySelector(selector);
    if (actionSection) {
      console.log('Found container with selector:', selector);
      break;
    }
  }
  
  if (!actionSection) {
    console.log('Could not find action section');
    return;
  }

  // ボタンをアクションセクションに追加
  actionSection.appendChild(saveButton);
  actionSection.appendChild(style);

  // ボタンクリック時のイベントリスナー
  saveButton.addEventListener('click', async () => {
    try {
      // ボタンを "loading" 状態に
      saveButton.classList.add('loading');
      saveButton.textContent = 'ダウンロード中...';

      // 現在のページのURLを取得
      const videoUrl = window.location.href;

      // 音声抽出リクエスト
      const response = await fetch('http://localhost:7783/api/v1/extract-audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ url: videoUrl })
      });

      // レスポンスチェック
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '音声抽出に失敗しました');
      }

      // Blobとしてレスポンスを取得
      const blob = await response.blob();

      // ダウンロードリンクを作成
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // デフォルトのファイル名を生成（動画タイトルや現在の日時を使用）
      const defaultFileName = `youtube-audio-${new Date().toISOString().replace(/[:.]/g, '-')}.mp3`;
      
      // ダウンロードリンクを作成
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = defaultFileName;
      
      // リンクを非表示で追加し、クリック
      document.body.appendChild(link);
      link.click();
      
      // リンクを削除
      document.body.removeChild(link);

      // ボタンを通常の状態に戻す
      saveButton.classList.remove('loading');
      saveButton.textContent = 'MP3を保存';

      alert('MP3ファイルが保存されました');
    } catch (error) {
      // ボタンを通常の状態に戻す
      saveButton.classList.remove('loading');
      saveButton.textContent = 'MP3を保存';

      // エラー処理
      console.error('音声抽出エラー:', error);
      alert(`エラーが発生しました: ${error.message}`);
    }
  });
}

// ページ読み込み時に実行
addMp3SaveButton();

// YouTubeの動的なページ読み込みに対応するため、定期的にチェック
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList') {
      // ボタンがない場合のみ追加
      if (!document.getElementById('mp3-save-button')) {
        addMp3SaveButton();
      }
    }
  });
});

// ページ全体の変更を監視
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// 初期読み込み後、1秒後にもう一度試行（動的コンテンツ対応）
setTimeout(addMp3SaveButton, 1000);