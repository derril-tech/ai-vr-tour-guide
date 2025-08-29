import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';
import { User } from '../../database/entities/user.entity';

@Injectable()
export class TenantGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const user: User = request.user;
    const tenantId = request.params.tenantId || request.body.tenantId || request.query.tenantId;

    if (!user) {
      return false;
    }

    // If no tenant ID is specified in the request, allow (will use user's tenant)
    if (!tenantId) {
      return true;
    }

    // Check if user belongs to the requested tenant
    if (user.tenantId !== tenantId) {
      throw new ForbiddenException('Access denied to this tenant');
    }

    return true;
  }
}
