"use client"
import React, { useState } from 'react';

export default function YouTubeAudioExtractor() {
  const [videoUrl, setVideoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadLink, setDownloadLink] = useState<string | null>(null);

  const extractAudio = async () => {
    // Reset previous states
    setError(null);
    setDownloadLink(null);
    setIsLoading(true);

    try {
      // Validate URL 
      if (!videoUrl.trim()) {
        throw new Error('Please enter a YouTube URL');
      }

      // Basic YouTube URL validation
      const youtubeUrlRegex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
      if (!youtubeUrlRegex.test(videoUrl)) {
        throw new Error('Invalid YouTube URL');
      }

      // Call the audio extraction API
      // const response = await fetch('https://my-yt-dlp-server.onrender.com/api/v1/extract-audio', {
      const response = await fetch('http://localhost:7783/api/v1/extract-audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ url: videoUrl })
      });

      if (!response.ok) {
        throw new Error('Audio extraction failed');
      }

      // Create a blob URL for download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // Extract filename from Content-Disposition header
      const filename = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'extracted-audio.mp3';

      // Create a temporary link for download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();

      setDownloadLink(downloadUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white shadow-md rounded-lg">
      <h1 className="text-2xl font-bold mb-4 text-center">YouTube Audio Extractor</h1>
      
      <div className="flex space-x-2 mb-4">
        <input 
          type="text" 
          placeholder="Enter YouTube Video URL" 
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          className="flex-grow px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          onClick={extractAudio} 
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-blue-300 transition-colors"
        >
          {isLoading ? 'Extracting...' : 'Extract Audio'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {downloadLink && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Success: </strong>
          <span className="block sm:inline">Your audio file has been downloaded successfully.</span>
        </div>
      )}
    </div>
  );
}