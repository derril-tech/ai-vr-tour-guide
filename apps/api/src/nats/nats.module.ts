import { Module, Global } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NatsService } from './nats.service';

@Global()
@Module({
  providers: [
    {
      provide: 'NATS_CLIENT',
      useFactory: async (configService: ConfigService) => {
        const { connect } = await import('nats');
        const nc = await connect({
          servers: configService.get('NATS_URL') || 'nats://localhost:4222',
        });
        return nc;
      },
      inject: [ConfigService],
    },
    NatsService,
  ],
  exports: ['NATS_CLIENT', NatsService],
})
export class NatsModule {}
