import { Router } from 'express';

export const userRoutes = Router();

userRoutes.get('/status', (_req, res) => {
  res.json({ ok: true });
});
