import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Site } from '../database/entities/site.entity';

@Injectable()
export class SitesService {
  constructor(
    @InjectRepository(Site)
    private readonly siteRepository: Repository<Site>,
  ) {}

  async findAll(tenantId: string): Promise<Site[]> {
    return this.siteRepository.find({
      where: { tenantId },
      order: { createdAt: 'DESC' },
    });
  }

  async findOne(id: string, tenantId: string): Promise<Site> {
    return this.siteRepository.findOne({
      where: { id, tenantId },
      relations: ['documents'],
    });
  }

  async create(createSiteDto: Partial<Site>): Promise<Site> {
    const site = this.siteRepository.create(createSiteDto);
    return this.siteRepository.save(site);
  }
}
