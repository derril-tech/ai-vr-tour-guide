import { Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { StorageService } from './storage.service';

@Module({
  providers: [
    {
      provide: 'S3_CLIENT',
      useFactory: async (configService: ConfigService) => {
        const { S3Client } = await import('@aws-sdk/client-s3');
        return new S3Client({
          region: configService.get('S3_REGION') || 'us-east-1',
          credentials: {
            accessKeyId: configService.get('S3_ACCESS_KEY_ID') || 'minioadmin',
            secretAccessKey: configService.get('S3_SECRET_ACCESS_KEY') || 'minioadmin',
          },
          endpoint: configService.get('S3_ENDPOINT') || 'http://localhost:9000',
          forcePathStyle: true, // Required for MinIO
        });
      },
      inject: [ConfigService],
    },
    StorageService,
  ],
  exports: [StorageService],
})
export class StorageModule {}
