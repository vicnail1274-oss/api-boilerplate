import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { authRoutes } from './routes/auth.routes';
import { userRoutes } from './routes/users.routes';
import { errorHandler } from './middleware/errorHandler';
import { logger } from './lib/logger';

const app = express();

// Security middleware
app.use(helmet());
app.use(cors());
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

// Global error handler (must be last)
app.use(errorHandler);

const PORT = process.env.PORT ?? 4000;
app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
});

export default app;
