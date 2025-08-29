import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { CasbinService } from '../../casbin/casbin.service';
import { User } from '../../database/entities/user.entity';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private casbinService: CasbinService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>('permissions', [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredPermissions) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user: User = request.user;

    if (!user) {
      return false;
    }

    // Check each required permission
    for (const permission of requiredPermissions) {
      const [resource, action] = permission.split(':');
      const hasPermission = await this.casbinService.enforce(
        user.role,
        resource,
        action,
      );

      if (!hasPermission) {
        return false;
      }
    }

    return true;
  }
}
