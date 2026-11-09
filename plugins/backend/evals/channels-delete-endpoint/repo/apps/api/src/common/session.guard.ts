import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common';
import type { FastifyRequest } from 'fastify';

export interface SessionUser {
  id: number;
  workspaceId: number;
}

// Reads the opaque session cookie and attaches the user to the request; 401 when there is none.
@Injectable()
export class SessionGuard implements CanActivate {
  async canActivate(ctx: ExecutionContext): Promise<boolean> {
    const req = ctx.switchToHttp().getRequest<FastifyRequest & { user?: SessionUser }>();
    const user = await lookupSession(req.headers.cookie);
    if (!user) throw new UnauthorizedException();
    req.user = user;
    return true;
  }
}

async function lookupSession(cookie: string | undefined): Promise<SessionUser | null> {
  // Fixture: the sessions table lookup lives here in the real app.
  return cookie ? null : null;
}
