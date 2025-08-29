import { Injectable, Inject, Logger } from '@nestjs/common';
import { NatsConnection, StringCodec } from 'nats';

@Injectable()
export class NatsService {
  private readonly logger = new Logger(NatsService.name);
  private readonly sc = StringCodec();

  constructor(
    @Inject('NATS_CLIENT') private readonly natsClient: NatsConnection,
  ) {}

  async publish(subject: string, data: any): Promise<void> {
    try {
      const payload = JSON.stringify(data);
      this.natsClient.publish(subject, this.sc.encode(payload));
      this.logger.debug(`Published to ${subject}: ${payload}`);
    } catch (error) {
      this.logger.error(`Failed to publish to ${subject}:`, error);
      throw error;
    }
  }

  async request(subject: string, data: any, timeout = 5000): Promise<any> {
    try {
      const payload = JSON.stringify(data);
      const response = await this.natsClient.request(
        subject,
        this.sc.encode(payload),
        { timeout },
      );
      const result = JSON.parse(this.sc.decode(response.data));
      this.logger.debug(`Request to ${subject} completed`);
      return result;
    } catch (error) {
      this.logger.error(`Failed to request ${subject}:`, error);
      throw error;
    }
  }

  subscribe(subject: string, callback: (data: any) => void | Promise<void>) {
    const subscription = this.natsClient.subscribe(subject);
    
    (async () => {
      for await (const msg of subscription) {
        try {
          const data = JSON.parse(this.sc.decode(msg.data));
          await callback(data);
        } catch (error) {
          this.logger.error(`Error processing message from ${subject}:`, error);
        }
      }
    })();

    return subscription;
  }

  async close(): Promise<void> {
    await this.natsClient.close();
  }
}
