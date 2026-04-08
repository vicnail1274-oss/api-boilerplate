import express from 'express';
import request from 'supertest';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { requireAdminDbSession } from './requireAdminDbSession';
import * as adminSessionService from '../services/adminSession.service';
import { errorHandler } from './errorHandler';

describe('requireAdminDbSession', () => {
  const app = express();
  app.get('/admin-only', requireAdminDbSession, (_req, res) => {
    res.json({ ok: true });
  });
  app.use(errorHandler);

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('returns 401 when no session token is provided', async () => {
    const response = await request(app).get('/admin-only');

    expect(response.status).toBe(401);
    expect(response.body.error).toContain('Admin session is required');
  });

  it('does not trust client-side role cookie when DB role is non-admin', async () => {
    vi.spyOn(adminSessionService, 'resolveSessionRoleFromDb').mockResolvedValue({
      sessionId: 's1',
      userId: 'u1',
      role: 'member',
    });

    const response = await request(app)
      .get('/admin-only')
      .set('Cookie', ['admin_session=session-token-1', 'role=admin']);

    expect(response.status).toBe(403);
    expect(response.body.error).toContain('Admin permission is required');
  });

  it('allows request when DB verifies admin role', async () => {
    vi.spyOn(adminSessionService, 'resolveSessionRoleFromDb').mockResolvedValue({
      sessionId: 's2',
      userId: 'u2',
      role: 'admin',
    });

    const response = await request(app)
      .get('/admin-only')
      .set('Cookie', ['admin_session=session-token-2', 'role=member']);

    expect(response.status).toBe(200);
    expect(response.body.ok).toBe(true);
  });
});
