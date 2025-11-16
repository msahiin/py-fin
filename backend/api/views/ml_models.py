"""
Machine Learning Models API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, MLModel
from api.schemas import ModelTrainRequest, ModelPredictionRequest, ModelPredictionResponse
from auth import get_current_user
from tasks import train_ml_model

router = APIRouter()


@router.post("/train")
def train_model(
    request: ModelTrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start training a machine learning model
    """
    data_params = {
        'interval': request.interval,
        'start_date': request.start_date,
        'end_date': request.end_date
    }

    # Start Celery task
    task = train_ml_model.delay(
        request.model_type,
        request.symbol,
        data_params
    )

    return {
        "message": f"Training started for {request.model_type} model",
        "task_id": task.id,
        "model_type": request.model_type,
        "symbol": request.symbol
    }


@router.get("/models", response_model=List[dict])
def get_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of trained models
    """
    models = db.query(MLModel).order_by(MLModel.trained_at.desc()).limit(50).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "version": m.version,
            "accuracy": m.accuracy,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "is_active": m.is_active,
            "trained_at": m.trained_at
        }
        for m in models
    ]


@router.post("/predict", response_model=ModelPredictionResponse)
def predict(
    request: ModelPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make prediction using trained model
    """
    from datetime import datetime
    from data.collectors import DataAggregator
    from data.processors import DataProcessor
    import pickle
    import os

    # Get latest active model
    model_record = db.query(MLModel).filter(
        MLModel.model_type == request.model_type,
        MLModel.is_active == True
    ).order_by(MLModel.trained_at.desc()).first()

    if not model_record:
        raise HTTPException(
            status_code=404,
            detail=f"No active {request.model_type} model found"
        )

    # Load model
    if not os.path.exists(model_record.model_path):
        raise HTTPException(status_code=500, detail="Model file not found")

    try:
        # Collect recent data
        aggregator = DataAggregator()
        df = aggregator.get_data(
            symbol=request.symbol,
            source='binance',
            interval=request.timeframe
        )

        if df.empty:
            raise HTTPException(status_code=400, detail="No data available")

        # Process data
        processor = DataProcessor()
        df = processor.clean_data(df)
        df = processor.add_technical_indicators(df)
        df = processor.add_price_features(df)

        # Prepare features
        df = df.dropna()
        if len(df) < 10:
            raise HTTPException(status_code=400, detail="Insufficient data for prediction")

        # Get last row for prediction
        X = df.tail(1).drop(columns=['open', 'high', 'low', 'close', 'volume'], errors='ignore')

        # Make prediction based on model type
        if request.model_type == 'xgboost':
            with open(model_record.model_path, 'rb') as f:
                model = pickle.load(f)

            prediction = model.predict(X)[0]
            probabilities = model.predict_proba(X)[0]

            # Map prediction
            direction_map = {0: 'sell', 1: 'hold', 2: 'buy'}
            direction = direction_map.get(prediction, 'hold')
            confidence = float(max(probabilities)) * 100

        else:
            # Default response for other models
            direction = 'hold'
            confidence = 50.0

        return {
            "symbol": request.symbol,
            "prediction": direction,
            "confidence": confidence,
            "predicted_price": None,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.delete("/models/{model_id}")
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a machine learning model
    """
    model = db.query(MLModel).filter(MLModel.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    db.delete(model)
    db.commit()

    return {"message": "Model deleted", "id": model_id}


@router.post("/models/{model_id}/activate")
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activate a model (deactivate others of same type)
    """
    model = db.query(MLModel).filter(MLModel.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Deactivate other models of same type
    db.query(MLModel).filter(
        MLModel.model_type == model.model_type,
        MLModel.id != model_id
    ).update({"is_active": False})

    # Activate this model
    model.is_active = True

    db.commit()

    return {"message": "Model activated", "id": model_id}
