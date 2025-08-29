import { Module } from '@nestjs/common';
import { AccessibilityController } from './accessibility.controller';
import { AccessibilityService } from './accessibility.service';
import { SubtitleService } from './subtitle.service';
import { FontService } from './font.service';
import { HandTrackingService } from './hand-tracking.service';
import { ContrastService } from './contrast.service';

@Module({
  controllers: [AccessibilityController],
  providers: [
    AccessibilityService,
    SubtitleService,
    FontService,
    HandTrackingService,
    ContrastService,
  ],
  exports: [AccessibilityService],
})
export class AccessibilityModule {}
