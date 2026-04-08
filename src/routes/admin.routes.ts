import { Router } from 'express';
import { requireAdminDbSession } from '../middleware/requireAdminDbSession';

export const adminRoutes = Router();

adminRoutes.get('/session', requireAdminDbSession, (req, res) => {
  const adminSession = (req as typeof req & {
    adminSession?: { sessionId: string; userId: string; role: string };
  }).adminSession;

  res.json({
    ok: true,
    session: adminSession,
  });
});
