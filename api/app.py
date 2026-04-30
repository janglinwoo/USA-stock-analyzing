from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import time
from typing import List, Optional

from api.models import (
    PredictionRequest,
    PredictionResponse,
    PredictionHistoryResponse,
    StatusResponse,
    JobStatus,
    PerformanceMetricsResponse,
    EventResponse,
    SentimentSummaryResponse,
    HealthCheckResponse,
)
from pipeline import RealtimePipeline
from pipeline.scheduler import PredictionScheduler
from database import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="USA Stock Analyzing API",
    description="Real-time stock price prediction using sentiment analysis and ML",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
db = None
pipeline = None
scheduler = None
start_time = datetime.now()


@app.on_event("startup")
async def startup_event():
    """Initialize database and pipeline on startup."""
    global db, pipeline, scheduler

    logger.info("Starting up API...")

    try:
        # Initialize database
        db = Database(db_url="sqlite:///./stock_predictions.db")
        logger.info("Database initialized")

        # Initialize pipeline
        pipeline = RealtimePipeline(db)
        logger.info("Pipeline initialized")

        # Initialize scheduler
        scheduler = PredictionScheduler()
        logger.info("Scheduler initialized")

    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global scheduler, db

    logger.info("Shutting down...")

    try:
        if scheduler and scheduler.is_running:
            scheduler.stop()

        if db:
            db.close()

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# ===== Health & Status Endpoints =====


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    global db, pipeline

    components = {
        "database": "connected" if db else "disconnected",
        "pipeline": "ready" if pipeline else "not_ready",
        "scheduler": "running" if scheduler and scheduler.is_running else "stopped",
    }

    return HealthCheckResponse(
        status="healthy",
        message="System is operational",
        timestamp=datetime.now(),
        components=components,
    )


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get system status."""
    global db, scheduler

    try:
        uptime = (datetime.now() - start_time).total_seconds()
        recent_preds = 0

        if db:
            session = db.get_session()
            from database import Prediction
            from sqlalchemy import func
            recent_preds = (
                session.query(func.count(Prediction.id))
                .filter(
                    Prediction.prediction_date
                    >= datetime.now() - timedelta(hours=24)
                )
                .scalar()
            )
            session.close()

        return StatusResponse(
            status="running",
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            scheduled_jobs=len(scheduler.get_jobs()) if scheduler else 0,
            recent_predictions_count=recent_preds,
            database_connected=db is not None,
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Prediction Endpoints =====


@app.post("/predict", response_model=PredictionResponse)
async def predict_single(request: PredictionRequest) -> PredictionResponse:
    """Make a prediction for a single stock."""
    global pipeline

    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    try:
        result = pipeline.predict_single_stock(request.ticker)

        if not result:
            raise HTTPException(status_code=404, detail=f"Could not predict {request.ticker}")

        return PredictionResponse(**result)

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{ticker}", response_model=PredictionHistoryResponse)
async def get_predictions(
    ticker: str, limit: int = 10, days_back: int = 30
) -> PredictionHistoryResponse:
    """Get prediction history for a ticker."""
    global db

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session = db.get_session()
        predictions = db.get_latest_predictions(session, ticker.upper(), limit=limit)

        response_predictions = [
            PredictionResponse(
                ticker=p.ticker,
                prediction_date=p.prediction_date,
                direction_prediction=p.direction_prediction,
                direction_confidence=p.direction_confidence or 0,
                predicted_price_change=p.predicted_price_change or 0,
                predicted_price_range_low=p.predicted_price_range_low or 0,
                predicted_price_range_high=p.predicted_price_range_high or 0,
                current_price=p.current_price or 0,
                combined_sentiment=p.combined_sentiment or 0,
                momentum_score=p.momentum_score or 0,
                model_version=p.model_version or "unknown",
            )
            for p in predictions
        ]

        session.close()

        return PredictionHistoryResponse(
            ticker=ticker.upper(),
            predictions=response_predictions,
            total_count=len(response_predictions),
        )

    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{ticker}/latest", response_model=PredictionResponse)
async def get_latest_prediction(ticker: str) -> PredictionResponse:
    """Get latest prediction for a ticker."""
    global db

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session = db.get_session()
        predictions = db.get_latest_predictions(session, ticker.upper(), limit=1)

        if not predictions:
            raise HTTPException(status_code=404, detail=f"No predictions found for {ticker}")

        p = predictions[0]
        session.close()

        return PredictionResponse(
            ticker=p.ticker,
            prediction_date=p.prediction_date,
            direction_prediction=p.direction_prediction,
            direction_confidence=p.direction_confidence or 0,
            predicted_price_change=p.predicted_price_change or 0,
            predicted_price_range_low=p.predicted_price_range_low or 0,
            predicted_price_range_high=p.predicted_price_range_high or 0,
            current_price=p.current_price or 0,
            combined_sentiment=p.combined_sentiment or 0,
            momentum_score=p.momentum_score or 0,
            model_version=p.model_version or "unknown",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Scheduler Endpoints =====


@app.post("/scheduler/start")
async def start_scheduler():
    """Start the prediction scheduler."""
    global scheduler, pipeline

    if not scheduler or not pipeline:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        scheduler.start()

        # Add hourly prediction job
        scheduler.add_hourly_job(
            lambda: pipeline.run_full_pipeline(days_back=1),
            job_id="hourly_prediction",
        )

        return {"status": "started", "message": "Scheduler is now running"}

    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the prediction scheduler."""
    global scheduler

    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        scheduler.stop()
        return {"status": "stopped", "message": "Scheduler has been stopped"}

    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduler/jobs", response_model=List[JobStatus])
async def get_scheduled_jobs() -> List[JobStatus]:
    """Get list of scheduled jobs."""
    global scheduler

    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        jobs = scheduler.get_jobs()

        return [
            JobStatus(
                job_id=job.id,
                job_name=job.name,
                is_active=job.trigger is not None,
                next_run_time=job.next_run_time,
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Pipeline Endpoints =====


@app.post("/pipeline/run")
async def run_pipeline(days_back: int = 1, background_tasks: BackgroundTasks = None):
    """Run the full prediction pipeline."""
    global pipeline

    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    try:
        # Run in background
        if background_tasks:
            background_tasks.add_task(pipeline.run_full_pipeline, days_back)
            return {"status": "running", "message": "Pipeline started in background"}
        else:
            results = pipeline.run_full_pipeline(days_back)
            return {
                "status": "completed",
                "predictions_count": len(results),
                "message": "Pipeline execution completed",
            }

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Performance Endpoints =====


@app.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics() -> PerformanceMetricsResponse:
    """Get latest model performance metrics."""
    global db

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session = db.get_session()
        metric = db.get_latest_metrics(session)
        session.close()

        if not metric:
            raise HTTPException(status_code=404, detail="No performance metrics available")

        return PerformanceMetricsResponse(
            metric_date=metric.metric_date,
            accuracy=metric.accuracy,
            precision=metric.precision,
            recall=metric.recall,
            f1_score=metric.f1_score,
            rmse=metric.rmse,
            r2_score=metric.r2_score,
            win_rate=metric.win_rate,
            total_return=metric.total_return,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accuracy/{days_back}")
async def get_prediction_accuracy(days_back: int = 30) -> dict:
    """Get prediction accuracy for recent predictions."""
    global db

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session = db.get_session()
        accuracy = db.get_prediction_accuracy(session, days_back=days_back)
        session.close()

        return accuracy

    except Exception as e:
        logger.error(f"Error getting accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
