"""
ML Model Loader Utilities for UK Bus Analytics Dashboard
========================================================
Load and use trained ML models with caching

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import pickle
import streamlit as st
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / 'models'


@st.cache_resource
def load_route_clustering_model():
    """
    Load route clustering model (Sentence Transformers + HDBSCAN)

    Returns:
        dict: Model artifacts including embeddings_model, clusterer, etc.
    """
    model_file = MODELS_DIR / 'route_clustering.pkl'
    with open(model_file, 'rb') as f:
        model_artifacts = pickle.load(f)
    return model_artifacts


@st.cache_resource
def load_anomaly_detector():
    """
    Load anomaly detection model (Isolation Forest)

    Returns:
        dict: Model artifacts including model, scaler, features
    """
    model_file = MODELS_DIR / 'anomaly_detector.pkl'
    with open(model_file, 'rb') as f:
        model_artifacts = pickle.load(f)
    return model_artifacts


@st.cache_resource
def load_coverage_predictor():
    """
    Load coverage prediction model (Random Forest)

    Returns:
        dict: Model artifacts including model, features, feature_importance
    """
    model_file = MODELS_DIR / 'coverage_predictor.pkl'
    with open(model_file, 'rb') as f:
        model_artifacts = pickle.load(f)
    return model_artifacts


def predict_coverage(model_artifacts, demographics_data):
    """
    Predict coverage score for new areas using trained model

    Args:
        model_artifacts: Loaded coverage prediction model
        demographics_data: DataFrame with demographic features

    Returns:
        array: Predicted coverage scores
    """
    model = model_artifacts['model']
    features = model_artifacts['features']

    # Ensure all required features are present
    X = demographics_data[features].fillna(0)

    predictions = model.predict(X)
    return predictions


def detect_anomalies(model_artifacts, lsoa_data):
    """
    Detect underserved areas using anomaly detection model

    Args:
        model_artifacts: Loaded anomaly detection model
        lsoa_data: DataFrame with LSOA metrics

    Returns:
        tuple: (anomaly_labels, anomaly_scores)
    """
    model = model_artifacts['model']
    scaler = model_artifacts['scaler']
    features = model_artifacts['features']

    # Prepare data
    X = lsoa_data[features].fillna(0)
    X_scaled = scaler.transform(X)

    # Predict
    labels = model.predict(X_scaled)
    scores = model.score_samples(X_scaled)

    return labels, scores
