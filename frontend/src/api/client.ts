import axios, { AxiosInstance } from 'axios';
import {
  Prediction,
  PredictionHistory,
  SystemStatus,
  JobStatus,
  PerformanceMetrics,
  HealthCheck,
  PredictionAccuracy,
} from '@types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Health & Status
  async healthCheck(): Promise<HealthCheck> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getStatus(): Promise<SystemStatus> {
    const response = await this.client.get('/status');
    return response.data;
  }

  // Predictions
  async makePrediction(ticker: string, days_back?: number): Promise<Prediction> {
    const response = await this.client.post('/predict', {
      ticker,
      days_back: days_back || 1,
    });
    return response.data;
  }

  async getPredictionHistory(
    ticker: string,
    limit: number = 10,
    days_back: number = 30
  ): Promise<PredictionHistory> {
    const response = await this.client.get(
      `/predictions/${ticker}?limit=${limit}&days_back=${days_back}`
    );
    return response.data;
  }

  async getLatestPrediction(ticker: string): Promise<Prediction> {
    const response = await this.client.get(`/predictions/${ticker}/latest`);
    return response.data;
  }

  // Scheduler
  async startScheduler(): Promise<{ status: string; message: string }> {
    const response = await this.client.post('/scheduler/start');
    return response.data;
  }

  async stopScheduler(): Promise<{ status: string; message: string }> {
    const response = await this.client.post('/scheduler/stop');
    return response.data;
  }

  async getScheduledJobs(): Promise<JobStatus[]> {
    const response = await this.client.get('/scheduler/jobs');
    return response.data;
  }

  // Pipeline
  async runPipeline(days_back?: number): Promise<{
    status: string;
    predictions_count?: number;
    message: string;
  }> {
    const response = await this.client.post('/pipeline/run', {
      days_back: days_back || 1,
    });
    return response.data;
  }

  // Performance
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    const response = await this.client.get('/performance');
    return response.data;
  }

  async getPredictionAccuracy(days_back: number = 30): Promise<PredictionAccuracy> {
    const response = await this.client.get(`/accuracy/${days_back}`);
    return response.data;
  }

  // Polling for real-time updates
  startPolling(
    callback: (status: SystemStatus) => void,
    interval: number = 30000
  ): () => void {
    const pollInterval = setInterval(async () => {
      try {
        const status = await this.getStatus();
        callback(status);
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, interval);

    return () => clearInterval(pollInterval);
  }
}

export const apiClient = new ApiClient();
