"""
Utility functions for AI decision-making module

Shared utilities for feature extraction, normalization, and common operations.
"""

import numpy as np
from typing import Any, Dict, List


def pad_or_truncate_features(features: np.ndarray, target_size: int) -> np.ndarray:
    """
    Pad or truncate feature vector to target size
    
    Args:
        features: Input feature array
        target_size: Desired feature vector size
        
    Returns:
        Feature array of target size
    """
    if len(features) < target_size:
        # Pad with zeros
        padded = np.zeros(target_size)
        padded[:len(features)] = features
        return padded
    else:
        # Truncate
        return features[:target_size]


def normalize_features(features: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
    """
    Normalize feature values to a specified range
    
    Args:
        features: Input features
        min_val: Minimum value for normalization
        max_val: Maximum value for normalization
        
    Returns:
        Normalized features
    """
    feature_min = np.min(features)
    feature_max = np.max(features)
    
    if feature_max - feature_min == 0:
        return np.full_like(features, (min_val + max_val) / 2)
    
    normalized = (features - feature_min) / (feature_max - feature_min)
    return normalized * (max_val - min_val) + min_val


def extract_numeric_features(data_dict: Dict[str, Any], max_features: int = 50) -> np.ndarray:
    """
    Extract numeric features from a dictionary
    
    Args:
        data_dict: Dictionary containing data
        max_features: Maximum number of features to extract
        
    Returns:
        Array of numeric features
    """
    features = []
    
    for key, value in data_dict.items():
        if isinstance(value, (int, float)):
            features.append(float(value))
        elif isinstance(value, bool):
            features.append(1.0 if value else 0.0)
    
    # Pad or truncate to max_features
    feature_array = np.array(features[:max_features])
    return pad_or_truncate_features(feature_array, max_features)


def calculate_risk_score(risk_factors: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    """
    Calculate weighted risk score from risk factors
    
    Args:
        risk_factors: Dictionary of risk factor names to values
        weights: Optional weights for each risk factor
        
    Returns:
        Weighted risk score between 0 and 1
    """
    if not risk_factors:
        return 0.0
    
    if weights is None:
        # Equal weights
        weights = {key: 1.0 for key in risk_factors}
    
    total_weighted_risk = 0.0
    total_weight = 0.0
    
    for risk_type, risk_value in risk_factors.items():
        weight = weights.get(risk_type, 1.0)
        total_weighted_risk += risk_value * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return total_weighted_risk / total_weight


def moving_average(data: List[float], window_size: int) -> np.ndarray:
    """
    Calculate moving average of data
    
    Args:
        data: Input data
        window_size: Size of moving average window
        
    Returns:
        Moving averages
    """
    if len(data) < window_size:
        return np.array([np.mean(data)] * len(data))
    
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')


def detect_outliers_zscore(data: List[float], threshold: float = 3.0) -> List[int]:
    """
    Detect outliers using z-score method
    
    Args:
        data: Input data
        threshold: Z-score threshold for outliers
        
    Returns:
        Indices of outliers
    """
    if len(data) < 3:
        return []
    
    data_array = np.array(data)
    mean = np.mean(data_array)
    std = np.std(data_array)
    
    if std == 0:
        return []
    
    z_scores = np.abs((data_array - mean) / std)
    outlier_indices = np.where(z_scores > threshold)[0]
    
    return outlier_indices.tolist()


def exponential_smoothing(data: List[float], alpha: float = 0.3) -> np.ndarray:
    """
    Apply exponential smoothing to data
    
    Args:
        data: Input data
        alpha: Smoothing factor (0 < alpha < 1)
        
    Returns:
        Smoothed data
    """
    if not data:
        return np.array([])
    
    smoothed = np.zeros(len(data))
    smoothed[0] = data[0]
    
    for i in range(1, len(data)):
        smoothed[i] = alpha * data[i] + (1 - alpha) * smoothed[i - 1]
    
    return smoothed
