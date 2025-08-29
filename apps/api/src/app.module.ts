import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';

// Core modules
import { AuthModule } from './auth/auth.module';
import { SitesModule } from './sites/sites.module';
import { ToursModule } from './tours/tours.module';
import { ContentModule } from './content/content.module';
import { SessionsModule } from './sessions/sessions.module';
import { TelemetryModule } from './telemetry/telemetry.module';

// Infrastructure modules
import { DatabaseModule } from './database/database.module';
import { RedisModule } from './redis/redis.module';
import { NatsModule } from './nats/nats.module';
import { StorageModule } from './storage/storage.module';

// Common modules
import { HealthModule } from './health/health.module';
import { CasbinModule } from './casbin/casbin.module';

import { appConfig } from './config/app.config';
import { databaseConfig } from './config/database.config';
import { redisConfig } from './config/redis.config';
import { jwtConfig } from './config/jwt.config';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      load: [appConfig, databaseConfig, redisConfig, jwtConfig],
      envFilePath: ['.env.local', '.env'],
    }),

    // Database
    DatabaseModule,
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        url: configService.get('database.url'),
        autoLoadEntities: true,
        synchronize: configService.get('app.env') === 'development',
        logging: configService.get('app.env') === 'development',
        ssl: configService.get('app.env') === 'production' ? { rejectUnauthorized: false } : false,
      }),
      inject: [ConfigService],
    }),

    // Authentication
    PassportModule.register({ defaultStrategy: 'jwt' }),
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        secret: configService.get('jwt.secret'),
        signOptions: {
          expiresIn: configService.get('jwt.expiresIn'),
        },
      }),
      inject: [ConfigService],
    }),

    // Infrastructure
    RedisModule,
    NatsModule,
    StorageModule,

    // Security
    CasbinModule,

    // Core business modules
    AuthModule,
    SitesModule,
    ToursModule,
    ContentModule,
    SessionsModule,
    TelemetryModule,

    // Utility modules
    HealthModule,
  ],
})
export class AppModule {}
