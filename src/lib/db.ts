import type { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma?: PrismaClient;
};

export function getDb(): PrismaClient {
  if (globalForPrisma.prisma) {
    return globalForPrisma.prisma;
  }

  // Lazy init avoids hard failure in test environments that do not generate Prisma client.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { PrismaClient: PrismaClientCtor } = require('@prisma/client') as { PrismaClient: new () => PrismaClient };
  const client = new PrismaClientCtor();

  if (process.env.NODE_ENV !== 'production') {
    globalForPrisma.prisma = client;
  }

  return client;
}
