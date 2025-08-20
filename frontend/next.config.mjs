/** @type {import('next').NextConfig} */
const nextConfig = {
  serverRuntimeConfig: {
    keepAliveTimeout: 120000,
  },
};

export default nextConfig;
