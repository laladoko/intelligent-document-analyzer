/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8081/api/:path*',
      },
    ];
  },

  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ];
  },
  
  // 优化实验性功能配置
  experimental: {
    serverActions: {
      bodySizeLimit: '50mb',
    },
  },
  
  // 处理大文件上传
  serverRuntimeConfig: {
    maxFileSize: '50mb',
  },
  
  publicRuntimeConfig: {
    maxFileSize: '50mb',
  },
};

module.exports = nextConfig; 