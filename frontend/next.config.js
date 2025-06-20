/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  
  // 简化配置，移除可能导致问题的选项
  typescript: {
    ignoreBuildErrors: false,
  },
  
  eslint: {
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig; 