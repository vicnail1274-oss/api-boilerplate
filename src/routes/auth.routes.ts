import { Router } from 'express';

export const authRoutes = Router();

authRoutes.get('/status', (_req, res) => {
  res.json({ ok: true });
});
