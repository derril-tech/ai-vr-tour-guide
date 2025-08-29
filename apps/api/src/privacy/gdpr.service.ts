import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../database/entities/user.entity';
import { Site } from '../database/entities/site.entity';
import { Document } from '../database/entities/document.entity';
import { EncryptionService } from './encryption.service';

interface GdprExportData {
  personalData: any;
  activityData: any;
  contentData: any;
  preferences: any;
  exportDate: string;
  dataRetentionInfo: any;
}

interface GdprDeletionReport {
  userId: string;
  tenantId: string;
  deletedRecords: {
    users: number;
    sites: number;
    documents: number;
    sessions: number;
    telemetry: number;
  };
  anonymizedRecords: {
    analytics: number;
    aggregated: number;
  };
  deletionDate: string;
  verificationHash: string;
}

@Injectable()
export class GdprService {
  private readonly logger = new Logger(GdprService.name);

  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    @InjectRepository(Site)
    private siteRepository: Repository<Site>,
    @InjectRepository(Document)
    private documentRepository: Repository<Document>,
    private encryptionService: EncryptionService,
  ) {}

  /**
   * Export all user data (GDPR Article 20 - Right to data portability)
   */
  async exportUserData(userId: string, tenantId: string): Promise<GdprExportData> {
    try {
      this.logger.log(`Starting GDPR data export for user ${userId}`);

      // Get user personal data
      const user = await this.userRepository.findOne({
        where: { id: userId, tenantId },
      });

      if (!user) {
        throw new Error('User not found');
      }

      // Decrypt sensitive data for export
      const decryptedUser = await this.encryptionService.decryptUserData(user, tenantId);

      // Get user's sites
      const sites = await this.siteRepository.find({
        where: { createdBy: userId, tenantId },
      });

      // Get user's documents
      const documents = await this.documentRepository.find({
        where: { tenantId }, // Additional filtering would be needed for user-specific docs
      });

      // Get activity data (would query telemetry/session tables)
      const activityData = await this.getUserActivityData(userId, tenantId);

      // Get user preferences
      const preferences = await this.getUserPreferences(userId, tenantId);

      const exportData: GdprExportData = {
        personalData: {
          id: decryptedUser.id,
          email: decryptedUser.email,
          name: decryptedUser.name,
          createdAt: decryptedUser.createdAt,
          lastLoginAt: decryptedUser.lastLoginAt,
          preferences: decryptedUser.preferences,
        },
        activityData,
        contentData: {
          sites: sites.map(site => ({
            id: site.id,
            name: site.name,
            description: site.description,
            createdAt: site.createdAt,
            updatedAt: site.updatedAt,
          })),
          documentsCount: documents.length,
        },
        preferences,
        exportDate: new Date().toISOString(),
        dataRetentionInfo: {
          personalDataRetention: '7 years',
          activityDataRetention: '2 years',
          anonymizedDataRetention: 'indefinite',
        },
      };

      this.logger.log(`GDPR data export completed for user ${userId}`);
      return exportData;

    } catch (error) {
      this.logger.error(`GDPR data export failed for user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Delete all user data (GDPR Article 17 - Right to erasure)
   */
  async deleteUserData(userId: string, tenantId: string, keepAnonymized: boolean = true): Promise<GdprDeletionReport> {
    try {
      this.logger.log(`Starting GDPR data deletion for user ${userId}`);

      const deletionReport: GdprDeletionReport = {
        userId,
        tenantId,
        deletedRecords: {
          users: 0,
          sites: 0,
          documents: 0,
          sessions: 0,
          telemetry: 0,
        },
        anonymizedRecords: {
          analytics: 0,
          aggregated: 0,
        },
        deletionDate: new Date().toISOString(),
        verificationHash: '',
      };

      // Delete user record
      const userDeleteResult = await this.userRepository.delete({
        id: userId,
        tenantId,
      });
      deletionReport.deletedRecords.users = userDeleteResult.affected || 0;

      // Delete or anonymize user's sites
      const userSites = await this.siteRepository.find({
        where: { createdBy: userId, tenantId },
      });

      for (const site of userSites) {
        if (keepAnonymized) {
          // Anonymize instead of delete
          await this.siteRepository.update(site.id, {
            createdBy: this.encryptionService.anonymizeData(userId, tenantId),
            name: `Anonymized Site ${site.id.substring(0, 8)}`,
            description: 'Content anonymized per GDPR request',
          });
        } else {
          await this.siteRepository.delete(site.id);
          deletionReport.deletedRecords.sites++;
        }
      }

      // Delete user sessions (would be in a sessions table)
      deletionReport.deletedRecords.sessions = await this.deleteUserSessions(userId, tenantId);

      // Delete or anonymize telemetry data
      const telemetryResult = await this.deleteUserTelemetry(userId, tenantId, keepAnonymized);
      deletionReport.deletedRecords.telemetry = telemetryResult.deleted;
      deletionReport.anonymizedRecords.analytics = telemetryResult.anonymized;

      // Secure deletion of encryption keys
      await this.encryptionService.secureDelete(tenantId);

      // Generate verification hash
      deletionReport.verificationHash = this.generateDeletionVerificationHash(deletionReport);

      this.logger.log(`GDPR data deletion completed for user ${userId}`);
      return deletionReport;

    } catch (error) {
      this.logger.error(`GDPR data deletion failed for user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Anonymize user data while preserving analytics value
   */
  async anonymizeUserData(userId: string, tenantId: string): Promise<void> {
    try {
      this.logger.log(`Starting data anonymization for user ${userId}`);

      const anonymizedId = this.encryptionService.anonymizeData(userId, tenantId);

      // Update user record with anonymized data
      await this.userRepository.update(
        { id: userId, tenantId },
        {
          email: `anonymized-${anonymizedId.substring(0, 8)}@example.com`,
          name: `Anonymous User ${anonymizedId.substring(0, 8)}`,
          preferences: {},
        }
      );

      // Anonymize related records
      await this.anonymizeUserSites(userId, tenantId, anonymizedId);
      await this.anonymizeUserTelemetry(userId, tenantId, anonymizedId);

      this.logger.log(`Data anonymization completed for user ${userId}`);

    } catch (error) {
      this.logger.error(`Data anonymization failed for user ${userId}:`, error);
      throw error;
    }
  }

  /**
   * Check data retention compliance
   */
  async checkDataRetentionCompliance(tenantId: string): Promise<any> {
    const retentionPolicies = {
      personalData: 7 * 365, // 7 years in days
      activityData: 2 * 365, // 2 years in days
      sessionData: 1 * 365,  // 1 year in days
    };

    const now = new Date();
    const compliance = {
      personalDataExpired: [],
      activityDataExpired: [],
      sessionDataExpired: [],
    };

    // Check for expired personal data
    const expiredUsers = await this.userRepository
      .createQueryBuilder('user')
      .where('user.tenantId = :tenantId', { tenantId })
      .andWhere('user.lastLoginAt < :expiredDate', {
        expiredDate: new Date(now.getTime() - retentionPolicies.personalData * 24 * 60 * 60 * 1000)
      })
      .getMany();

    compliance.personalDataExpired = expiredUsers.map(user => ({
      userId: user.id,
      lastLogin: user.lastLoginAt,
      daysExpired: Math.floor((now.getTime() - user.lastLoginAt.getTime()) / (24 * 60 * 60 * 1000))
    }));

    return compliance;
  }

  // Helper methods

  private async getUserActivityData(userId: string, tenantId: string): Promise<any> {
    // This would query telemetry/activity tables
    return {
      sessionsCount: 0,
      totalDuration: 0,
      sitesVisited: [],
      lastActivity: null,
    };
  }

  private async getUserPreferences(userId: string, tenantId: string): Promise<any> {
    // This would query user preferences
    return {
      language: 'en',
      accessibility: [],
      notifications: {},
    };
  }

  private async deleteUserSessions(userId: string, tenantId: string): Promise<number> {
    // This would delete from sessions table
    return 0;
  }

  private async deleteUserTelemetry(userId: string, tenantId: string, keepAnonymized: boolean): Promise<{ deleted: number; anonymized: number }> {
    // This would delete/anonymize telemetry data
    return { deleted: 0, anonymized: 0 };
  }

  private async anonymizeUserSites(userId: string, tenantId: string, anonymizedId: string): Promise<void> {
    await this.siteRepository.update(
      { createdBy: userId, tenantId },
      { createdBy: anonymizedId }
    );
  }

  private async anonymizeUserTelemetry(userId: string, tenantId: string, anonymizedId: string): Promise<void> {
    // This would anonymize telemetry records
  }

  private generateDeletionVerificationHash(report: GdprDeletionReport): string {
    const data = JSON.stringify({
      userId: report.userId,
      tenantId: report.tenantId,
      deletedRecords: report.deletedRecords,
      deletionDate: report.deletionDate,
    });
    
    return require('crypto').createHash('sha256').update(data).digest('hex');
  }
}
