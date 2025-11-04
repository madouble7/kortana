import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import githubRoutes from './routes/github';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API Routes
app.use('/api/github', githubRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Kor\'tana service is running' });
});

// Serve static files from React app in production
// Note: In production on Cloud Run, this is protected by Cloud Run's built-in rate limiting
// For additional protection, consider using express-rate-limit middleware
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/build', 'index.html'));
  });
}

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Kor'tana server is running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

export default app;
