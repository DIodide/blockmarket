# BlockMarket Master Server

Express.js server for the BlockMarket decentralized marketplace backend.

## Features

- 🚀 **Express.js** - Fast, unopinionated web framework
- 🔒 **Security** - Helmet for security headers, rate limiting
- 🌐 **CORS** - Cross-origin resource sharing support
- 📝 **Logging** - Morgan HTTP request logger
- 🗜️ **Compression** - Gzip compression for responses
- ⚡ **Hot Reload** - Nodemon for development
- 🏥 **Health Checks** - Built-in health monitoring endpoints

## Getting Started

### Prerequisites
- Node.js (version 16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Start the development server:
```bash
npm run dev
```

4. Start the production server:
```bash
npm start
```

The server will be available at `http://localhost:5000`

### Available Scripts

- `npm start` - Start production server
- `npm run dev` - Start development server with hot reload

### API Endpoints

#### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system information

#### Core API
- `GET /api` - API information and available endpoints
- `GET /api/marketplace` - Get marketplace items
- `POST /api/marketplace` - Create new marketplace item
- `GET /api/users` - Get users
- `GET /api/transactions` - Get transactions

#### Root
- `GET /` - Server information

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `PORT` - Server port (default: 5000)
- `NODE_ENV` - Environment (development/production)
- `FRONTEND_URL` - Frontend URL for CORS (default: http://localhost:3000)

### Project Structure

```
├── server.js           # Main server file
├── routes/
│   ├── api.js         # API routes
│   └── health.js      # Health check routes
├── package.json       # Dependencies and scripts
├── .env.example       # Environment variables template
└── README.md         # This file
```

## Security Features

- **Helmet** - Sets various HTTP headers
- **Rate Limiting** - 100 requests per 15 minutes per IP
- **CORS** - Configured for frontend origin
- **Request Size Limits** - 10MB limit for JSON/URL-encoded data

## Development

The server includes comprehensive error handling, logging, and development-friendly features like detailed error messages in development mode.
