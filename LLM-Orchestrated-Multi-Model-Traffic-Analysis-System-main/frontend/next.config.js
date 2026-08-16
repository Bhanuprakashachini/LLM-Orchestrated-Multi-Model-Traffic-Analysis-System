/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  // Suppress ALL development warnings and noise
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  experimental: {
    forceSwcTransforms: true,
  },
  // Minimize console output
  logging: {
    fetches: {
      fullUrl: false,
    },
  },
  // Suppress webpack warnings
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.infrastructureLogging = {
        level: 'error',
      }
      config.stats = 'errors-only'
    }
    return config
  },
  // Suppress TypeScript errors during development
  typescript: {
    ignoreBuildErrors: false,
  },
  // Suppress ESLint during builds
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig