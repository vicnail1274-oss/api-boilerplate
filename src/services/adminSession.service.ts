import { Prisma } from '@prisma/client';
import { db } from '../lib/db';

type SessionLookupRow = {
  session_id: string | number;
  user_id: string | number;
  role: string;
};

export type AdminSessionContext = {
  sessionId: string;
  userId: string;
  role: string;
};

const SESSION_COOKIE_NAME = process.env.ADMIN_SESSION_COOKIE_NAME ?? 'admin_session';
function readCookie(rawCookie: string, key: string): string | null {
  const segments = rawCookie.split(';');

  for (const segment of segments) {
    const [cookieKey, ...cookieValue] = segment.trim().split('=');
    if (cookieKey === key) {
      const value = cookieValue.join('=').trim();
      return value.length > 0 ? decodeURIComponent(value) : null;
    }
  }

  return null;
}

function isSchemaMismatchError(error: unknown): boolean {
  const message = error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
  return (
    message.includes('does not exist') ||
    message.includes('no such table') ||
    message.includes('unknown table') ||
    message.includes('unknown column') ||
    (message.includes('column') && message.includes('does not exist'))
  );
}

export function extractAdminSessionToken(rawCookieHeader: string | undefined, rawSessionHeader: string | string[] | undefined): string | null {
  if (typeof rawSessionHeader === 'string' && rawSessionHeader.trim().length > 0) {
    return rawSessionHeader.trim();
  }

  if (!rawCookieHeader) {
    return null;
  }

  return readCookie(rawCookieHeader, SESSION_COOKIE_NAME);
}

async function runLookupQuery(query: Prisma.Sql): Promise<AdminSessionContext | null> {
  const rows = await db.$queryRaw<SessionLookupRow[]>(query);
  if (!rows[0]) {
    return null;
  }

  return {
    sessionId: String(rows[0].session_id),
    userId: String(rows[0].user_id),
    role: rows[0].role,
  };
}

export async function resolveSessionRoleFromDb(sessionToken: string): Promise<AdminSessionContext | null> {
  const lookupQueries: Prisma.Sql[] = [
    Prisma.sql`
      SELECT s.id AS session_id, s.user_id AS user_id, u.role AS role
      FROM admin_sessions s
      JOIN users u ON u.id = s.user_id
      WHERE s.session_token = ${sessionToken}
        AND s.revoked_at IS NULL
        AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
      LIMIT 1
    `,
    Prisma.sql`
      SELECT s.id AS session_id, s.user_id AS user_id, u.role AS role
      FROM sessions s
      JOIN users u ON u.id = s.user_id
      WHERE s.token = ${sessionToken}
        AND s.revoked_at IS NULL
        AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
      LIMIT 1
    `,
  ];

  let lastError: unknown;
  for (const query of lookupQueries) {
    try {
      return await runLookupQuery(query);
    } catch (error) {
      if (isSchemaMismatchError(error)) {
        lastError = error;
        continue;
      }

      throw error;
    }
  }

  if (lastError) {
    throw lastError;
  }

  return null;
}
