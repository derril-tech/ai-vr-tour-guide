import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  OneToMany,
  JoinColumn,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';
import { Tenant } from './tenant.entity';
import { Document } from './document.entity';

@Entity('sites', { schema: 'content' })
export class Site {
  @ApiProperty({ description: 'Unique identifier' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty({ description: 'Tenant ID' })
  @Column('uuid', { name: 'tenant_id' })
  tenantId: string;

  @ApiProperty({ description: 'Site name' })
  @Column({ length: 255 })
  name: string;

  @ApiProperty({ description: 'Site description' })
  @Column('text', { nullable: true })
  description: string;

  @ApiProperty({ description: 'Geographic location (lat, lng)' })
  @Column('point', { nullable: true })
  location: string;

  @ApiProperty({ description: 'Site metadata and configuration' })
  @Column('jsonb', { default: {} })
  metadata: Record<string, any>;

  @ApiProperty({ description: 'Creation timestamp' })
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @ApiProperty({ description: 'Last update timestamp' })
  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relations
  @ManyToOne(() => Tenant, (tenant) => tenant.sites)
  @JoinColumn({ name: 'tenant_id' })
  tenant: Tenant;

  @OneToMany(() => Document, (document) => document.site)
  documents: Document[];
}
