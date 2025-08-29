import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { PrivacyController } from './privacy.controller';
import { PrivacyService } from './privacy.service';
import { EncryptionService } from './encryption.service';
import { GdprService } from './gdpr.service';
import { DataRetentionService } from './data-retention.service';
import { User } from '../database/entities/user.entity';
import { Site } from '../database/entities/site.entity';
import { Document } from '../database/entities/document.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User, Site, Document])],
  controllers: [PrivacyController],
  providers: [
    PrivacyService,
    EncryptionService,
    GdprService,
    DataRetentionService,
  ],
  exports: [PrivacyService, EncryptionService, GdprService],
})
export class PrivacyModule {}
