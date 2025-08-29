import { Injectable, UnauthorizedException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';

import { User } from '../database/entities/user.entity';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';

@Injectable()
export class AuthService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
    private readonly jwtService: JwtService,
  ) {}

  async register(registerDto: RegisterDto) {
    const { email, password, name, tenantId } = registerDto;

    // Check if user already exists
    const existingUser = await this.userRepository.findOne({
      where: { email },
    });

    if (existingUser) {
      throw new UnauthorizedException('User already exists');
    }

    // Hash password
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // Create user
    const user = this.userRepository.create({
      email,
      name,
      tenantId,
      passwordHash,
    });

    await this.userRepository.save(user);

    // Generate JWT token
    const payload = { sub: user.id, email: user.email, tenantId: user.tenantId };
    const accessToken = this.jwtService.sign(payload);

    return {
      accessToken,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
        tenantId: user.tenantId,
      },
    };
  }

  async login(loginDto: LoginDto) {
    const { email, password } = loginDto;

    // Find user
    const user = await this.userRepository.findOne({
      where: { email },
      select: ['id', 'email', 'name', 'role', 'tenantId', 'passwordHash'],
    });

    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Generate JWT token
    const payload = { sub: user.id, email: user.email, tenantId: user.tenantId };
    const accessToken = this.jwtService.sign(payload);

    return {
      accessToken,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
        tenantId: user.tenantId,
      },
    };
  }

  async validateUser(userId: string): Promise<User | null> {
    return this.userRepository.findOne({
      where: { id: userId },
      relations: ['tenant'],
    });
  }

  async findOrCreateOidcUser(userInfo: { email: string; name: string; sub: string }): Promise<User> {
    let user = await this.userRepository.findOne({
      where: { email: userInfo.email },
      relations: ['tenant'],
    });

    if (!user) {
      // For new OIDC users, assign to default tenant
      // In production, you might want more sophisticated tenant assignment logic
      const defaultTenant = await this.userRepository.manager.findOne('Tenant', {
        where: { slug: 'dev' },
      });

      if (!defaultTenant) {
        throw new Error('Default tenant not found');
      }

      user = this.userRepository.create({
        email: userInfo.email,
        name: userInfo.name,
        tenantId: defaultTenant.id,
        metadata: { oidcSub: userInfo.sub },
      });

      await this.userRepository.save(user);
    }

    return user;
  }

  generateToken(payload: any): string {
    return this.jwtService.sign(payload);
  }
}
