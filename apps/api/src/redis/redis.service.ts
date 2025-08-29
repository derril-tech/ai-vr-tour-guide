import { Injectable, Inject } from '@nestjs/common';
import { RedisClientType } from 'redis';

@Injectable()
export class RedisService {
  constructor(
    @Inject('REDIS_CLIENT') private readonly redisClient: RedisClientType,
  ) {}

  async get(key: string): Promise<string | null> {
    return this.redisClient.get(key);
  }

  async set(key: string, value: string, ttl?: number): Promise<void> {
    if (ttl) {
      await this.redisClient.setEx(key, ttl, value);
    } else {
      await this.redisClient.set(key, value);
    }
  }

  async del(key: string): Promise<number> {
    return this.redisClient.del(key);
  }

  async exists(key: string): Promise<number> {
    return this.redisClient.exists(key);
  }

  async hGet(key: string, field: string): Promise<string | undefined> {
    return this.redisClient.hGet(key, field);
  }

  async hSet(key: string, field: string, value: string): Promise<number> {
    return this.redisClient.hSet(key, field, value);
  }

  async hGetAll(key: string): Promise<Record<string, string>> {
    return this.redisClient.hGetAll(key);
  }

  async expire(key: string, seconds: number): Promise<boolean> {
    return this.redisClient.expire(key, seconds);
  }

  async incr(key: string): Promise<number> {
    return this.redisClient.incr(key);
  }

  async decr(key: string): Promise<number> {
    return this.redisClient.decr(key);
  }

  async sadd(key: string, ...members: string[]): Promise<number> {
    return this.redisClient.sAdd(key, members);
  }

  async smembers(key: string): Promise<string[]> {
    return this.redisClient.sMembers(key);
  }

  async srem(key: string, ...members: string[]): Promise<number> {
    return this.redisClient.sRem(key, members);
  }
}
