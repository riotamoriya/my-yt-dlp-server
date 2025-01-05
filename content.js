function addDarkOverlayButton() {
  // 既に追加されていないか確認
  const existingButton = document.getElementById('dark-overlay-button');
  if (existingButton) return;

  // デバッグ用のコンソールログ
  console.log('Adding dark overlay button');

  // 動画の下にあるセクションを見つける
  // YouTubeのページ構造が変更されている可能性があるため、複数のセレクタを試す
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

  // ボタン要素を作成
  const overlayButton = document.createElement('button');
  overlayButton.id = 'dark-overlay-button';
  overlayButton.textContent = '画面を暗くする';
  overlayButton.classList.add('dark-overlay-btn');

  // ボタンをアクションセクションに追加
  actionSection.appendChild(overlayButton);
  console.log('Button added to the page');

  // ボタンクリック時のイベントリスナー
  overlayButton.addEventListener('click', () => {
    // 既に存在する場合は削除、なければ追加
    const existingOverlay = document.getElementById('dark-overlay');
    if (existingOverlay) {
      existingOverlay.remove();
    } else {
      const overlay = document.createElement('div');
      overlay.id = 'dark-overlay';
      document.body.appendChild(overlay);

      // オーバーレイクリック時にも削除できるようにする
      overlay.addEventListener('click', () => {
        overlay.remove();
      });
    }
  });
}

// ページ読み込み時に実行
addDarkOverlayButton();

// YouTubeの動的なページ読み込みに対応するため、定期的にチェック
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList') {
      // ボタンがない場合のみ追加
      if (!document.getElementById('dark-overlay-button')) {
        addDarkOverlayButton();
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
setTimeout(addDarkOverlayButton, 1000);