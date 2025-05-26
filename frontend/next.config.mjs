let userConfig = undefined
try {
  userConfig = await import('./v0-user-next.config')
} catch (e) {
  // ignore error
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
    domains: ['wonderful-water-06824e60f.6.azurestaticapps.net', 'localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'wonderful-water-06824e60f.6.azurestaticapps.net',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'juanchito-plaza.blueriver-8537145c.westus2.azurecontainerapps.io',
        pathname: '/**',
      },
    ],
  },
  experimental: {
    webpackBuildWorker: true,
    parallelServerBuildTraces: true,
    parallelServerCompiles: true,
  },
  env: {
    NEXT_PUBLIC_BACKEND_URL: 'https://juanchito-plaza.blueriver-8537145c.westus2.azurecontainerapps.io',
    NEXT_PUBLIC_API_URL: 'https://juanchito-plaza.blueriver-8537145c.westus2.azurecontainerapps.io'
  },
  // Asegurarse de que la aplicación se sirva desde la raíz
  basePath: '',
  trailingSlash: false,
}

mergeConfig(nextConfig, userConfig)

function mergeConfig(nextConfig, userConfig) {
  if (!userConfig) {
    return
  }

  for (const key in userConfig) {
    if (
      typeof nextConfig[key] === 'object' &&
      !Array.isArray(nextConfig[key])
    ) {
      nextConfig[key] = {
        ...nextConfig[key],
        ...userConfig[key],
      }
    } else {
      nextConfig[key] = userConfig[key]
    }
  }
}

export default nextConfig
