function addMp3SaveButton() {
  // 既に追加されていないか確認
  const existingButton = document.getElementById('mp3-save-button');
  if (existingButton) return;

  console.log('Adding MP3 save button');

  // ファイル名を取得する関数
  function getFilenameFromResponse(response) {
    const disposition = response.headers.get('content-disposition');
    console.log('Content-Disposition:', disposition); // デバッグ用

    if (disposition && disposition.includes('filename=')) {
      let filename = '';
      const matches = /filename\*=UTF-8''(.+)/.exec(disposition);
      if (matches && matches[1]) {
        filename = decodeURIComponent(matches[1]);
      } else {
        const matches = /filename="(.+)"/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }
      console.log('Extracted filename:', filename); // デバッグ用
      return filename || 'downloaded.mp3';
    }
    return 'downloaded.mp3';
  }

  // ボタン要素を作成
  const saveButton = document.createElement('button');
  saveButton.id = 'mp3-save-button';
  saveButton.textContent = 'MP3を保存';
  saveButton.classList.add('mp3-save-btn');

  // スタイル設定（既存のまま）
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

  // コンテナ検索（既存のまま）
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

  // 単一のイベントリスナー
  saveButton.addEventListener('click', async () => {
    try {
      saveButton.classList.add('loading');
      saveButton.textContent = 'ダウンロード中...';

      const videoUrl = window.location.href;
      const response = await fetch('http://localhost:7783/api/v1/extract-audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        },
        body: JSON.stringify({ url: videoUrl })
    });
    
    // レスポンスヘッダーをログ出力
    console.log('Response headers:', response.headers);
    console.log('Content-Disposition:', response.headers.get('content-disposition'));



      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '音声抽出に失敗しました');
      }

      const blob = await response.blob();
      const filename = getFilenameFromResponse(response);
      console.log('Using filename:', filename); // デバッグ用

      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      link.click();

      window.URL.revokeObjectURL(link.href);

      saveButton.classList.remove('loading');
      saveButton.textContent = 'MP3を保存';
      alert('MP3ファイルが保存されました');
    } catch (error) {
      saveButton.classList.remove('loading');
      saveButton.textContent = 'MP3を保存';
      console.error('音声抽出エラー:', error);
      alert(`エラーが発生しました: ${error.message}`);
    }
  });
}

// 既存の初期化コード
addMp3SaveButton();

const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList') {
      if (!document.getElementById('mp3-save-button')) {
        addMp3SaveButton();
      }
    }
  });
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

setTimeout(addMp3SaveButton, 1000);