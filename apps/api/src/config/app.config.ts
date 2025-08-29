import { registerAs } from '@nestjs/config';

export const appConfig = registerAs('app', () => ({
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT, 10) || 3000,
  corsOrigins: process.env.CORS_ORIGINS || 'http://localhost:3002,http://localhost:3003',
  logLevel: process.env.LOG_LEVEL || 'info',
}));
