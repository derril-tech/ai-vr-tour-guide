import { Module } from '@nestjs/common';
import { TestingController } from './testing.controller';
import { TestingService } from './testing.service';
import { UnitTestService } from './unit-test.service';
import { IntegrationTestService } from './integration-test.service';
import { E2ETestService } from './e2e-test.service';
import { ChaosTestService } from './chaos-test.service';
import { VRTestService } from './vr-test.service';

@Module({
  controllers: [TestingController],
  providers: [
    TestingService,
    UnitTestService,
    IntegrationTestService,
    E2ETestService,
    ChaosTestService,
    VRTestService,
  ],
  exports: [TestingService],
})
export class TestingModule {}
