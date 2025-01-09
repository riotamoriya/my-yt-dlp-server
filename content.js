// content.js
/*
 * YouTube MP3ダウンローダー Content Script
 * 
 * 設計思想：
 * - YouTube動画/プレイリストページおよび検索結果ページにMP3ダウンロードボタンを追加するContent Script
 * - シンプルで保守性の高いクラスベースのアーキテクチャを採用
 * - 各クラスは単一責任の原則に従い、明確な役割を持つ
 * 
 * 主要コンポーネント：
 * - Config: 設定値の集約による保守性の向上
 * - FileUtils: ファイル操作に関する共通処理
 * - AudioExtractorService: APIとの通信を担当
 * - DownloadManager: ダウンロード処理の統合管理
 * - MP3ButtonManager: UIコンポーネントとユーザーインタラクションの管理
 * - SearchResultsButtonManager: 検索結果ページのボタン管理
 * 
 * 拡張性：
 * - 新機能の追加が容易な構造
 * - APIエンドポイントの追加や変更が設定で完結
 * - UI要素の追加や変更が分離された形で可能
 */

// 設定の名前空間
const Config = {
  API: {
    BASE_URL: 'http://localhost:7783/api/v1',
    ENDPOINTS: {
      EXTRACT_AUDIO: '/extract-audio',
      EXTRACT_ALBUM: '/extract-album'
    }
  },
  UI: {
    BUTTON_STYLES: `
      .mp3-save-btn {
        display: block;
        margin: 10px auto;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease;
        color: white;
      }
      .mp3-save-btn:hover {
        filter: brightness(0.95);
      }
      .mp3-save-btn.loading {
        background-color: #ccc;
        cursor: wait;
      }
      .mp3-save-btn-search {
        display: inline-block;
        margin: 5px 0;
        padding: 8px 16px;
        font-size: 0.9em;
      }
    `,
    CONTAINER_SELECTORS: [
      'div#actions.ytd-video-primary-info-renderer',
      'div#actions-inner',
      'ytd-video-primary-info-renderer #actions',
      '#top-row.ytd-video-primary-info-renderer'
    ],
    SEARCH_RESULT_SELECTORS: {
      VIDEO_ITEMS: 'ytd-video-renderer',
      BUTTON_CONTAINER: '#meta',
      METADATA_CONTAINER: '#metadata-line'
    }
  }
};

// ユーティリティクラス
class FileUtils {
  static getFilenameFromResponse(response) {
    const disposition = response.headers.get('content-disposition');
    if (!disposition) return 'downloaded.mp3';

    const utf8Match = /filename\*=UTF-8''(.+)/.exec(disposition);
    if (utf8Match?.[1]) {
      return decodeURIComponent(utf8Match[1]);
    }

    const standardMatch = /filename="(.+)"/.exec(disposition);
    return standardMatch?.[1] || 'downloaded.mp3';
  }

  static async downloadBlob(blob, filename) {
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(link.href);
  }

  static getVideoIdFromElement(element) {
    const videoLink = element.querySelector('a#video-title');
    if (!videoLink) return null;
    
    const href = videoLink.href;
    const match = href.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
  }
}

// APIサービスクラス
class AudioExtractorService {
  async extractAudio(url, endpoint) {
    const response = await fetch(`${Config.API.BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': '*/*'
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '音声抽出に失敗しました');
    }

    return response;
  }
}

// ダウンロード管理クラス
class DownloadManager {
  constructor() {
    this.service = new AudioExtractorService();
  }

  async handleDownload(button, endpoint, successMessage, videoId = null) {
    const originalText = button.textContent;
    try {
      button.classList.add('loading');
      button.textContent = 'ダウンロード中...';

      const url = videoId 
        ? `https://www.youtube.com/watch?v=${videoId}`
        : window.location.href;

      const response = await this.service.extractAudio(
        url,
        endpoint
      );

      const blob = await response.blob();
      const filename = FileUtils.getFilenameFromResponse(response);
      await FileUtils.downloadBlob(blob, filename);

      alert(successMessage);
    } catch (error) {
      console.error('音声抽出エラー:', error);
      alert(`エラーが発生しました: ${error.message}`);
    } finally {
      button.classList.remove('loading');
      button.textContent = originalText;
    }
  }
}

// 検索結果ページのボタン管理クラス
class SearchResultsButtonManager {
  constructor() {
    this.downloadManager = new DownloadManager();
  }

  createSearchResultButton(videoId) {
    const button = document.createElement('button');
    button.textContent = 'MP3を保存';
    button.classList.add('mp3-save-btn', 'mp3-save-btn-search');
    button.style.backgroundColor = '#4CAF50';
    
    button.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.downloadManager.handleDownload(
        button,
        Config.API.ENDPOINTS.EXTRACT_AUDIO,
        'MP3ファイルが保存されました',
        videoId
      );
    });

    return button;
  }

  addButtonToSearchResult(videoElement) {
    // 既にボタンが追加されているか確認
    if (videoElement.querySelector('.mp3-save-btn')) {
      return;
    }

    const videoId = FileUtils.getVideoIdFromElement(videoElement);
    if (!videoId) {
      return;
    }

    const metadataContainer = videoElement.querySelector(
      Config.UI.SEARCH_RESULT_SELECTORS.METADATA_CONTAINER
    );
    if (!metadataContainer) {
      return;
    }

    const button = this.createSearchResultButton(videoId);
    metadataContainer.appendChild(button);
  }

  processSearchResults() {
    const videoItems = document.querySelectorAll(
      Config.UI.SEARCH_RESULT_SELECTORS.VIDEO_ITEMS
    );
    videoItems.forEach(item => this.addButtonToSearchResult(item));
  }
}

// メインの機能を管理するクラス
class MP3ButtonManager {
  constructor() {
    this.downloadManager = new DownloadManager();
  }

  createButton(id, text, backgroundColor) {
    const button = document.createElement('button');
    button.id = id;
    button.textContent = text;
    button.classList.add('mp3-save-btn');
    if (backgroundColor) {
      button.style.backgroundColor = backgroundColor;
    }
    return button;
  }

  addStyles() {
    const existingStyle = document.getElementById('mp3-button-styles');
    if (!existingStyle) {
      const style = document.createElement('style');
      style.id = 'mp3-button-styles';
      style.textContent = Config.UI.BUTTON_STYLES;
      document.head.appendChild(style);
    }
  }

  findContainer() {
    for (const selector of Config.UI.CONTAINER_SELECTORS) {
      const container = document.querySelector(selector);
      if (container) {
        return container;
      }
    }
    return null;
  }

  initialize() {
    // 既に追加されているか確認
    if (document.getElementById('mp3-save-button')) {
      return;
    }

    const container = this.findContainer();
    if (!container) {
      return;
    }

    this.addStyles();

    // 単曲ダウンロードボタン
    const singleButton = this.createButton(
      'mp3-save-button',
      'MP3を保存',
      '#4CAF50'
    );
    singleButton.addEventListener('click', () =>
      this.downloadManager.handleDownload(
        singleButton,
        Config.API.ENDPOINTS.EXTRACT_AUDIO,
        'MP3ファイルが保存されました'
      )
    );

    // プレイリストダウンロードボタン
    const playlistButton = this.createButton(
      'mp3-save-button-2',
      'プレイリストの全ての曲を保存',
      '#007BFF'
    );
    playlistButton.addEventListener('click', () =>
      this.downloadManager.handleDownload(
        playlistButton,
        Config.API.ENDPOINTS.EXTRACT_ALBUM,
        'プレイリストの全ての曲が保存されました'
      )
    );

    container.appendChild(singleButton);
    container.appendChild(playlistButton);
  }
}

// メイン処理
const buttonManager = new MP3ButtonManager();
const searchResultsManager = new SearchResultsButtonManager();

function initializeButtons() {
  buttonManager.addStyles();
  
  // 現在のページURLをチェック
  const isSearchPage = window.location.pathname === '/results';
  
  if (isSearchPage) {
    searchResultsManager.processSearchResults();
  } else {
    buttonManager.initialize();
  }
}

// 初期化処理の実行
initializeButtons();

// DOMの変更を監視
const observer = new MutationObserver((mutations) => {
  const isSearchPage = window.location.pathname === '/results';
  
  if (isSearchPage) {
    searchResultsManager.processSearchResults();
  } else {
    if (!document.getElementById('mp3-save-button')) {
      buttonManager.initialize();
    }
  }
});

// オブザーバーの設定
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// 遅延実行による初期化
setTimeout(() => initializeButtons(), 1000);