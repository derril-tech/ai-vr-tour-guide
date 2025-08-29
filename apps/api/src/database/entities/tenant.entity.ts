import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';
import { User } from './user.entity';
import { Site } from './site.entity';

@Entity('tenants')
export class Tenant {
  @ApiProperty({ description: 'Unique identifier' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty({ description: 'Tenant name' })
  @Column({ length: 255 })
  name: string;

  @ApiProperty({ description: 'URL-friendly slug' })
  @Column({ length: 100, unique: true })
  slug: string;

  @ApiProperty({ description: 'Tenant configuration settings' })
  @Column('jsonb', { default: {} })
  settings: Record<string, any>;

  @ApiProperty({ description: 'Creation timestamp' })
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @ApiProperty({ description: 'Last update timestamp' })
  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relations
  @OneToMany(() => User, (user) => user.tenant)
  users: User[];

  @OneToMany(() => Site, (site) => site.tenant)
  sites: Site[];
}
