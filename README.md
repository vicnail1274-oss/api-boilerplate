# API Boilerplate

![Node.js](https://img.shields.io/badge/Node.js-20-green?logo=node.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Express](https://img.shields.io/badge/Express-4-black?logo=express)
![Prisma](https://img.shields.io/badge/Prisma-5-2D3748?logo=prisma)
![Zod](https://img.shields.io/badge/Zod-3-3068b7)
![License](https://img.shields.io/badge/license-MIT-green)

Production-ready Express + TypeScript REST API with validation, auth middleware, error handling, and database access pre-wired.

---

## What's Included

| Feature | Implementation |
|---------|---------------|
| Framework | Express 4 |
| Language | TypeScript 5 |
| Validation | Zod schemas |
| ORM | Prisma 5 + PostgreSQL |
| Auth | JWT middleware |
| Error Handling | Centralized error handler |
| Logging | Winston structured logs |
| Rate Limiting | express-rate-limit |
| Testing | Vitest + Supertest |

---

## Quick Start

```bash
# Use this template
gh repo create my-api --template vicnail1274-oss/api-boilerplate --public

# Or clone directly
git clone https://github.com/vicnail1274-oss/api-boilerplate my-api
cd my-api

# Install
npm install

# Configure
cp .env.example .env
# Edit .env with your database URL and JWT secret

# Run migrations
npx prisma migrate dev

# Start dev server (with hot reload)
npm run dev
```

Server starts on [http://localhost:4000](http://localhost:4000)

---

## Project Structure

```
src/
├── controllers/        # Route handlers (thin — call services)
│   ├── auth.ts
│   └── users.ts
├── services/           # Business logic
│   ├── auth.service.ts
│   └── users.service.ts
├── middleware/         # Express middleware
│   ├── auth.ts         # JWT verification
│   ├── validate.ts     # Zod request validation
│   └── errorHandler.ts # Global error handler
├── routes/             # Route definitions
│   ├── auth.routes.ts
│   └── users.routes.ts
├── schemas/            # Zod validation schemas
│   ├── auth.schema.ts
│   └── users.schema.ts
├── lib/
│   ├── db.ts           # Prisma client singleton
│   ├── jwt.ts          # JWT helpers
│   └── logger.ts       # Winston logger
├── types/              # TypeScript types
└── app.ts              # Express app setup
prisma/
└── schema.prisma
```

---

## API Endpoints

```
POST   /api/auth/register    # Register new user
POST   /api/auth/login       # Login → returns JWT
GET    /api/auth/me          # Get current user (auth required)

GET    /api/users            # List users (admin only)
GET    /api/users/:id        # Get user by ID
PATCH  /api/users/:id        # Update user
DELETE /api/users/:id        # Delete user
```

---

## Validation Example

```typescript
// schemas/users.schema.ts
import { z } from 'zod';

export const createUserSchema = z.object({
  body: z.object({
    email: z.string().email(),
    name: z.string().min(2).max(100),
    password: z.string().min(8),
  }),
});

// routes/users.routes.ts
router.post('/', validate(createUserSchema), createUser);
```

---

## Environment Variables

```env
DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
JWT_SECRET="your-jwt-secret-min-32-chars"
JWT_EXPIRES_IN="7d"
PORT=4000
NODE_ENV="development"
LOG_LEVEL="debug"
```

---

## Scripts

```bash
npm run dev         # Start with hot reload (tsx watch)
npm run build       # Compile TypeScript
npm run start       # Run compiled output
npm run test        # Run Vitest tests
npm run test:cover  # Run tests with coverage
npm run lint        # ESLint
npm run db:migrate  # Prisma migrate dev
npm run db:studio   # Prisma Studio
```

---

## Testing

```bash
# Run all tests
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test:cover
```

---

## Useful Dev Tools

Speed up API development with these free tools from **[DevPlaybook](https://devplaybook.cc)**:

- [JSON Formatter](https://devplaybook.cc/tools/json-formatter) — Pretty-print API responses
- [JWT Decoder](https://devplaybook.cc/tools/jwt-decoder) — Inspect JWT payloads without a library
- [Base64 Encoder](https://devplaybook.cc/tools/base64) — Encode auth headers
- [UUID Generator](https://devplaybook.cc/tools/uuid) — Generate test IDs
- [Hash Generator](https://devplaybook.cc/tools/hash) — SHA256 / bcrypt checksums
- [All 40+ tools →](https://devplaybook.cc)

---

## Contributing

PRs welcome. Open an issue for major changes first.

## License

[MIT](LICENSE)
