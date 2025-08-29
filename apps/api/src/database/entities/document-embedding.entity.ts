import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';
import { Document } from './document.entity';

@Entity('document_embeddings', { schema: 'content' })
export class DocumentEmbedding {
  @ApiProperty({ description: 'Unique identifier' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty({ description: 'Document ID' })
  @Column('uuid', { name: 'document_id' })
  documentId: string;

  @ApiProperty({ description: 'Chunk index within document' })
  @Column('integer', { name: 'chunk_index' })
  chunkIndex: number;

  @ApiProperty({ description: 'Text content of the chunk' })
  @Column('text')
  content: string;

  @ApiProperty({ description: 'Vector embedding' })
  @Column('vector', { length: 1536 }) // OpenAI ada-002 dimension
  embedding: number[];

  @ApiProperty({ description: 'Chunk metadata' })
  @Column('jsonb', { default: {} })
  metadata: Record<string, any>;

  @ApiProperty({ description: 'Creation timestamp' })
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  // Relations
  @ManyToOne(() => Document, (document) => document.embeddings)
  @JoinColumn({ name: 'document_id' })
  document: Document;
}
