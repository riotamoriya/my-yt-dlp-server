/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/extract-audio',
        destination: 'http://localhost:7783/api/v1/extract-audio'
      }
    ];
  }
};

module.exports = nextConfig;