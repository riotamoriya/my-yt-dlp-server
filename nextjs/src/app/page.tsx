import Head from 'next/head';
import YouTubeAudioExtractor from '@/components/YouTubeAudioExtractor';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <Head>
        <title>YouTube Audio Extractor</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <YouTubeAudioExtractor />
      </div>
    </div>
  );
}