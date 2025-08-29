/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  webpack: (config) => {
    // Handle three.js and other 3D libraries
    config.externals = config.externals || []
    config.externals.push({
      'three': 'three',
    })
    
    return config
  },
}

module.exports = nextConfig
