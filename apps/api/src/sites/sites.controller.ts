import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { SitesService } from './sites.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RolesGuard } from '../auth/guards/roles.guard';
import { TenantGuard } from '../auth/guards/tenant.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { Permissions } from '../auth/decorators/permissions.decorator';
import { User } from '../database/entities/user.entity';

@ApiTags('sites')
@Controller('sites')
@UseGuards(JwtAuthGuard, TenantGuard, RolesGuard)
@ApiBearerAuth()
export class SitesController {
  constructor(private readonly sitesService: SitesService) {}

  @Get()
  @Permissions('sites:read')
  @ApiOperation({ summary: 'Get all sites for current tenant' })
  async findAll(@CurrentUser() user: User) {
    return this.sitesService.findAll(user.tenantId);
  }

  @Get(':id')
  @Permissions('sites:read')
  @ApiOperation({ summary: 'Get site by ID' })
  async findOne(@Param('id') id: string, @CurrentUser() user: User) {
    return this.sitesService.findOne(id, user.tenantId);
  }

  @Post()
  @Permissions('sites:create')
  @ApiOperation({ summary: 'Create a new site' })
  async create(@Body() createSiteDto: any, @CurrentUser() user: User) {
    return this.sitesService.create({ ...createSiteDto, tenantId: user.tenantId });
  }
}
