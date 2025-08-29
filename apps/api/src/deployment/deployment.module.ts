import { Module } from '@nestjs/common';
import { DeploymentController } from './deployment.controller';
import { DeploymentService } from './deployment.service';
import { MonitoringService } from './monitoring.service';
import { AlertingService } from './alerting.service';
import { HealthCheckService } from './health-check.service';

@Module({
  controllers: [DeploymentController],
  providers: [
    DeploymentService,
    MonitoringService,
    AlertingService,
    HealthCheckService,
  ],
  exports: [DeploymentService, MonitoringService],
})
export class DeploymentModule {}
