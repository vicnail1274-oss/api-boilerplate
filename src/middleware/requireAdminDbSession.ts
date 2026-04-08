import { NextFunction, Request, Response } from 'express';
import { AppError } from './errorHandler';
import { extractAdminSessionToken, resolveSessionRoleFromDb } from '../services/adminSession.service';

export async function requireAdminDbSession(req: Request, _res: Response, next: NextFunction) {
  const sessionToken = extractAdminSessionToken(req.headers.cookie, req.headers['x-admin-session']);
  if (!sessionToken) {
    return next(new AppError(401, 'Admin session is required'));
  }

  const session = await resolveSessionRoleFromDb(sessionToken);
  if (!session) {
    return next(new AppError(401, 'Admin session is invalid or expired'));
  }

  // Role must come from DB-backed session lookup; do not trust client-side cookies.
  if (session.role.toLowerCase() !== 'admin') {
    return next(new AppError(403, 'Admin permission is required'));
  }

  (req as Request & { adminSession?: typeof session }).adminSession = session;
  return next();
}
