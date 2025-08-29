import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as crypto from 'crypto';

interface EncryptionEnvelope {
  encryptedData: string;
  iv: string;
  keyId: string;
  algorithm: string;
  tenantId: string;
  timestamp: string;
}

@Injectable()
export class EncryptionService {
  private readonly logger = new Logger(EncryptionService.name);
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyCache = new Map<string, Buffer>();

  constructor(private configService: ConfigService) {}

  /**
   * Generate tenant-specific encryption key
   */
  private getTenantKey(tenantId: string): Buffer {
    const cacheKey = `tenant_${tenantId}`;
    
    if (this.keyCache.has(cacheKey)) {
      return this.keyCache.get(cacheKey)!;
    }

    // In production, this would use a proper key management service (AWS KMS, Azure Key Vault, etc.)
    const masterKey = this.configService.get<string>('ENCRYPTION_MASTER_KEY') || 'default-master-key-change-in-production';
    const tenantSalt = crypto.createHash('sha256').update(`${tenantId}-salt`).digest();
    
    const key = crypto.pbkdf2Sync(masterKey, tenantSalt, 100000, 32, 'sha256');
    this.keyCache.set(cacheKey, key);
    
    return key;
  }

  /**
   * Encrypt data with tenant-specific envelope
   */
  async encryptData(data: string, tenantId: string): Promise<EncryptionEnvelope> {
    try {
      const key = this.getTenantKey(tenantId);
      const iv = crypto.randomBytes(16);
      const keyId = crypto.createHash('sha256').update(`${tenantId}-${Date.now()}`).digest('hex').substring(0, 16);

      const cipher = crypto.createCipher(this.algorithm, key);
      cipher.setAAD(Buffer.from(tenantId)); // Additional authenticated data

      let encrypted = cipher.update(data, 'utf8', 'hex');
      encrypted += cipher.final('hex');

      const authTag = cipher.getAuthTag();
      const encryptedWithTag = encrypted + ':' + authTag.toString('hex');

      return {
        encryptedData: encryptedWithTag,
        iv: iv.toString('hex'),
        keyId,
        algorithm: this.algorithm,
        tenantId,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      this.logger.error(`Encryption failed for tenant ${tenantId}:`, error);
      throw new Error('Encryption failed');
    }
  }

  /**
   * Decrypt data from envelope
   */
  async decryptData(envelope: EncryptionEnvelope): Promise<string> {
    try {
      const key = this.getTenantKey(envelope.tenantId);
      const iv = Buffer.from(envelope.iv, 'hex');

      const [encryptedData, authTagHex] = envelope.encryptedData.split(':');
      const authTag = Buffer.from(authTagHex, 'hex');

      const decipher = crypto.createDecipher(envelope.algorithm, key);
      decipher.setAAD(Buffer.from(envelope.tenantId));
      decipher.setAuthTag(authTag);

      let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
      decrypted += decipher.final('utf8');

      return decrypted;
    } catch (error) {
      this.logger.error(`Decryption failed for tenant ${envelope.tenantId}:`, error);
      throw new Error('Decryption failed');
    }
  }

  /**
   * Encrypt sensitive user data
   */
  async encryptUserData(userData: any, tenantId: string): Promise<any> {
    const sensitiveFields = ['email', 'phone', 'address', 'personalInfo'];
    const encrypted = { ...userData };

    for (const field of sensitiveFields) {
      if (userData[field]) {
        encrypted[field] = await this.encryptData(
          JSON.stringify(userData[field]), 
          tenantId
        );
      }
    }

    return encrypted;
  }

  /**
   * Decrypt sensitive user data
   */
  async decryptUserData(encryptedData: any, tenantId: string): Promise<any> {
    const sensitiveFields = ['email', 'phone', 'address', 'personalInfo'];
    const decrypted = { ...encryptedData };

    for (const field of sensitiveFields) {
      if (encryptedData[field] && typeof encryptedData[field] === 'object') {
        const decryptedValue = await this.decryptData(encryptedData[field]);
        decrypted[field] = JSON.parse(decryptedValue);
      }
    }

    return decrypted;
  }

  /**
   * Generate data anonymization hash
   */
  anonymizeData(data: string, tenantId: string): string {
    const salt = crypto.createHash('sha256').update(`${tenantId}-anonymization`).digest();
    return crypto.pbkdf2Sync(data, salt, 10000, 32, 'sha256').toString('hex');
  }

  /**
   * Secure data deletion (cryptographic erasure)
   */
  async secureDelete(tenantId: string, keyId?: string): Promise<void> {
    try {
      if (keyId) {
        // Delete specific key
        this.keyCache.delete(`tenant_${tenantId}_${keyId}`);
      } else {
        // Delete all tenant keys
        for (const [key] of this.keyCache) {
          if (key.startsWith(`tenant_${tenantId}`)) {
            this.keyCache.delete(key);
          }
        }
      }

      this.logger.log(`Secure deletion completed for tenant ${tenantId}`);
    } catch (error) {
      this.logger.error(`Secure deletion failed for tenant ${tenantId}:`, error);
      throw error;
    }
  }
}
