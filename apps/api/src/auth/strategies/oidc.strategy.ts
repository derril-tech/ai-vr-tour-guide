import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy } from 'passport-oauth2';
import { ConfigService } from '@nestjs/config';
import { AuthService } from '../auth.service';

@Injectable()
export class OidcStrategy extends PassportStrategy(Strategy, 'oidc') {
  constructor(
    private readonly authService: AuthService,
    private readonly configService: ConfigService,
  ) {
    super({
      authorizationURL: `${configService.get('OIDC_ISSUER_URL')}/auth`,
      tokenURL: `${configService.get('OIDC_ISSUER_URL')}/token`,
      clientID: configService.get('OIDC_CLIENT_ID'),
      clientSecret: configService.get('OIDC_CLIENT_SECRET'),
      callbackURL: `${configService.get('API_BASE_URL')}/api/v1/auth/oidc/callback`,
      scope: ['openid', 'profile', 'email'],
    });
  }

  async validate(accessToken: string, refreshToken: string, profile: any) {
    // Extract user info from OIDC profile
    const userInfo = {
      email: profile.email,
      name: profile.name || profile.given_name + ' ' + profile.family_name,
      sub: profile.sub,
    };

    // Find or create user
    return this.authService.findOrCreateOidcUser(userInfo);
  }
}
