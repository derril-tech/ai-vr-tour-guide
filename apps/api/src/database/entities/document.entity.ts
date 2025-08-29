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
import { Site } from './site.entity';
import { DocumentEmbedding } from './document-embedding.entity';

@Entity('documents', { schema: 'content' })
export class Document {
  @ApiProperty({ description: 'Unique identifier' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty({ description: 'Tenant ID' })
  @Column('uuid', { name: 'tenant_id' })
  tenantId: string;

  @ApiProperty({ description: 'Site ID' })
  @Column('uuid', { name: 'site_id', nullable: true })
  siteId: string;

  @ApiProperty({ description: 'Document title' })
  @Column({ length: 255 })
  title: string;

  @ApiProperty({ description: 'Document content' })
  @Column('text', { nullable: true })
  content: string;

  @ApiProperty({ description: 'Content type/format' })
  @Column({ length: 100, name: 'content_type', nullable: true })
  contentType: string;

  @ApiProperty({ description: 'Source URL' })
  @Column('text', { name: 'source_url', nullable: true })
  sourceUrl: string;

  @ApiProperty({ description: 'Document metadata' })
  @Column('jsonb', { default: {} })
  metadata: Record<string, any>;

  @ApiProperty({ description: 'Creation timestamp' })
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @ApiProperty({ description: 'Last update timestamp' })
  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relations
  @ManyToOne(() => Tenant)
  @JoinColumn({ name: 'tenant_id' })
  tenant: Tenant;

  @ManyToOne(() => Site, (site) => site.documents)
  @JoinColumn({ name: 'site_id' })
  site: Site;

  @OneToMany(() => DocumentEmbedding, (embedding) => embedding.document)
  embeddings: DocumentEmbedding[];
}
