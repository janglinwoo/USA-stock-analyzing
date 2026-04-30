# Stock Prediction Dashboard - Frontend

React-based web dashboard for the USA Stock Analysis system.

## Features

- **Real-time System Status**: Monitor system health and database connectivity
- **Prediction Display**: View latest stock predictions with confidence scores
- **Sentiment Analysis**: Visualize combined sentiment from multiple sources
- **Technical Indicators**: Track RSI, momentum, and other indicators
- **Pipeline Control**: Manually trigger analysis or start/stop automatic scheduler
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Axios**: API client
- **React Router**: Navigation
- **Lucide Icons**: UI icons

## Setup

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update `.env` with API endpoint (default is localhost:8000):
```
REACT_APP_API_URL=http://localhost:8000
```

### Running the Dashboard

Development mode with hot reload:
```bash
npm start
```

The dashboard will open at `http://localhost:3000`

Production build:
```bash
npm run build
```

### API Integration

The dashboard communicates with the FastAPI backend via `src/api/client.ts`:

- **Health Check**: `/health`
- **System Status**: `/status`
- **Make Prediction**: `POST /predict`
- **Get Predictions**: `GET /predictions/{ticker}`
- **Run Pipeline**: `POST /pipeline/run`
- **Scheduler Control**: `POST /scheduler/start`, `POST /scheduler/stop`
- **Performance Metrics**: `GET /performance`

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── PredictionCard.tsx
│   │   └── SystemStatus.tsx
│   ├── pages/               # Page components
│   │   └── Dashboard.tsx
│   ├── api/                 # API client
│   │   └── client.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── styles/              # CSS files
│   │   └── index.css
│   ├── App.tsx              # Main component
│   └── index.tsx            # Entry point
├── public/
│   └── index.html
├── package.json
├── tsconfig.json
└── README.md
```

## Components

### PredictionCard
Displays a single stock prediction with:
- Direction (up/down) with confidence
- Current and predicted prices
- Price range estimate
- Sentiment and momentum scores

### SystemStatus
Shows system health:
- Running status
- Uptime
- Database connection status
- Recent prediction count
- Scheduled jobs

### Dashboard
Main page combining all components with:
- System status overview
- Action buttons (run pipeline, start/stop scheduler)
- Predictions grid
- Information about all phases

## Environment Variables

- `REACT_APP_API_URL`: Backend API endpoint (default: http://localhost:8000)

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deployment

The built dashboard can be served from any static hosting:

```bash
# Serve locally
npm install -g serve
serve -s build
```

Or deploy to Vercel, Netlify, GitHub Pages, etc.

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Advanced charting with historical data
- [ ] Stock watchlist management
- [ ] Email/SMS notifications
- [ ] Dark mode theme
- [ ] Multi-language support
- [ ] Export predictions to CSV
- [ ] Sentiment heatmap visualization

## Troubleshooting

### CORS Issues
If you get CORS errors, ensure the backend is running and `.env` has the correct `REACT_APP_API_URL`.

### API Connection Failed
Check that:
1. Backend is running on the configured port
2. `REACT_APP_API_URL` is correct
3. Firewall allows connections to the backend

### Hot Reload Not Working
```bash
rm -rf node_modules package-lock.json
npm install
npm start
```

## License

MIT
