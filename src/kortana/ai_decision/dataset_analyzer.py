"""
Dataset Analyzer - Time-sensitive data analysis for decision-making

This module provides real-time analysis of time-sensitive datasets,
extracting patterns, trends, and critical features for autonomous decision-making.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DatasetMetrics:
    """Metrics from dataset analysis"""

    size: int
    time_range: tuple[datetime, datetime]
    data_quality: float  # 0-1 score
    missing_values_ratio: float
    temporal_consistency: float  # 0-1 score
    key_features: dict[str, Any]


@dataclass
class TrendAnalysis:
    """Results of trend analysis"""

    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float  # 0-1 score
    anomalies: list[dict[str, Any]]
    seasonal_patterns: dict[str, Any]
    forecast: dict[str, Any]


class DatasetAnalyzer:
    """
    Analyzes time-sensitive datasets for decision-making

    Features:
    - Real-time data quality assessment
    - Temporal pattern detection
    - Anomaly detection
    - Trend analysis and forecasting
    - Feature extraction for ML models
    """

    def __init__(
        self,
        window_size: int = 100,
        anomaly_threshold: float = 2.5,
        enable_caching: bool = True,
    ):
        """
        Initialize the dataset analyzer

        Args:
            window_size: Size of sliding window for temporal analysis
            anomaly_threshold: Standard deviations for anomaly detection
            enable_caching: Whether to cache analysis results
        """
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        self.enable_caching = enable_caching
        self._cache: dict[str, Any] = {}

        logger.info(
            f"Dataset analyzer initialized (window_size={window_size}, "
            f"anomaly_threshold={anomaly_threshold})"
        )

    def analyze_dataset(
        self, data: list[dict[str, Any]], timestamp_key: str = "timestamp"
    ) -> DatasetMetrics:
        """
        Analyze a dataset and compute key metrics

        Args:
            data: List of data records
            timestamp_key: Key name for timestamp field

        Returns:
            Dataset metrics
        """
        if not data:
            logger.warning("Empty dataset provided")
            return DatasetMetrics(
                size=0,
                time_range=(datetime.now(), datetime.now()),
                data_quality=0.0,
                missing_values_ratio=1.0,
                temporal_consistency=0.0,
                key_features={},
            )

        logger.info(f"Analyzing dataset with {len(data)} records")

        # Extract timestamps
        timestamps = []
        for record in data:
            if timestamp_key in record:
                ts = record[timestamp_key]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                timestamps.append(ts)

        time_range = (
            min(timestamps) if timestamps else datetime.now(),
            max(timestamps) if timestamps else datetime.now(),
        )

        # Calculate data quality
        total_fields = sum(len(record) for record in data)
        missing_values = sum(
            1 for record in data for value in record.values() if value is None
        )
        missing_ratio = missing_values / total_fields if total_fields > 0 else 0.0
        data_quality = 1.0 - missing_ratio

        # Calculate temporal consistency
        if len(timestamps) > 1:
            time_diffs = [
                (timestamps[i + 1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]
            mean_diff = np.mean(time_diffs)
            std_diff = np.std(time_diffs)
            temporal_consistency = (
                1.0 - min(std_diff / mean_diff, 1.0) if mean_diff > 0 else 0.0
            )
        else:
            temporal_consistency = 1.0

        # Extract key features
        key_features = self._extract_key_features(data)

        metrics = DatasetMetrics(
            size=len(data),
            time_range=time_range,
            data_quality=data_quality,
            missing_values_ratio=missing_ratio,
            temporal_consistency=temporal_consistency,
            key_features=key_features,
        )

        logger.info(
            f"Dataset analysis complete: quality={data_quality:.2f}, "
            f"temporal_consistency={temporal_consistency:.2f}"
        )

        return metrics

    def _extract_key_features(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Extract key features from dataset

        Args:
            data: Dataset records

        Returns:
            Dictionary of key features
        """
        # Get all numeric fields
        numeric_fields = set()
        for record in data:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    numeric_fields.add(key)

        # Calculate statistics for each numeric field
        features = {}
        for field in numeric_fields:
            values = [
                record[field]
                for record in data
                if field in record and record[field] is not None
            ]
            if values:
                features[field] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "count": len(values),
                }

        return features

    def detect_anomalies(
        self, data: list[dict[str, Any]], field: str
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in a specific field

        Args:
            data: Dataset records
            field: Field name to analyze

        Returns:
            List of anomaly records
        """
        logger.info(f"Detecting anomalies in field: {field}")

        # Extract values
        values = []
        indices = []
        for i, record in enumerate(data):
            if field in record and isinstance(record[field], (int, float)):
                values.append(float(record[field]))
                indices.append(i)

        if len(values) < 3:
            logger.warning("Not enough data points for anomaly detection")
            return []

        values_array = np.array(values)
        mean = np.mean(values_array)
        std = np.std(values_array)

        # Detect outliers using z-score
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std) if std > 0 else 0
            if z_score > self.anomaly_threshold:
                anomalies.append(
                    {
                        "index": indices[i],
                        "value": value,
                        "z_score": float(z_score),
                        "record": data[indices[i]],
                    }
                )

        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies

    def analyze_trends(
        self, data: list[dict[str, Any]], field: str, timestamp_key: str = "timestamp"
    ) -> TrendAnalysis:
        """
        Analyze trends in a time-series field

        Args:
            data: Dataset records
            field: Field to analyze
            timestamp_key: Key for timestamp field

        Returns:
            Trend analysis results
        """
        logger.info(f"Analyzing trends for field: {field}")

        # Extract time-series data
        time_series = []
        for record in data:
            if field in record and timestamp_key in record:
                ts = record[timestamp_key]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                value = record[field]
                if isinstance(value, (int, float)):
                    time_series.append((ts, float(value)))

        if len(time_series) < 2:
            logger.warning("Insufficient data for trend analysis")
            return TrendAnalysis(
                trend_direction="unknown",
                trend_strength=0.0,
                anomalies=[],
                seasonal_patterns={},
                forecast={},
            )

        # Sort by timestamp
        time_series.sort(key=lambda x: x[0])

        # Extract values
        values = np.array([v for _, v in time_series])

        # Calculate trend using linear regression
        x = np.arange(len(values))
        z = np.polyfit(x, values, 1)
        slope = z[0]

        # Determine trend direction
        mean_value = np.mean(values)
        relative_slope = slope / mean_value if mean_value != 0 else 0

        if abs(relative_slope) < 0.01:
            trend_direction = "stable"
            trend_strength = 0.0
        elif relative_slope > 0.05:
            trend_direction = "increasing"
            trend_strength = min(abs(relative_slope), 1.0)
        elif relative_slope < -0.05:
            trend_direction = "decreasing"
            trend_strength = min(abs(relative_slope), 1.0)
        else:
            # Check for volatility
            volatility = np.std(values) / mean_value if mean_value != 0 else 0
            if volatility > 0.2:
                trend_direction = "volatile"
                trend_strength = min(volatility, 1.0)
            else:
                trend_direction = "stable"
                trend_strength = 0.0

        # Detect anomalies
        anomalies = self.detect_anomalies(data, field)

        # Simple forecast (next few values)
        p = np.poly1d(z)
        future_x = np.arange(len(values), len(values) + 5)
        forecast_values = p(future_x)

        forecast = {
            "horizon": 5,
            "values": forecast_values.tolist(),
            "confidence": 0.7,  # Simplified
        }

        # Detect seasonal patterns (simplified)
        seasonal_patterns = self._detect_seasonal_patterns(values)

        analysis = TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            anomalies=anomalies,
            seasonal_patterns=seasonal_patterns,
            forecast=forecast,
        )

        logger.info(
            f"Trend analysis complete: direction={trend_direction}, "
            f"strength={trend_strength:.2f}"
        )

        return analysis

    def _detect_seasonal_patterns(self, values: np.ndarray) -> dict[str, Any]:
        """
        Detect seasonal patterns in time-series data

        Args:
            values: Time-series values

        Returns:
            Seasonal pattern information
        """
        if len(values) < 10:
            return {"detected": False}

        # Simple autocorrelation-based pattern detection
        # In production, use more sophisticated methods like FFT or STL decomposition
        autocorr = np.correlate(values - np.mean(values), values - np.mean(values), mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]

        # Find peaks in autocorrelation
        peaks = []
        for i in range(1, min(len(autocorr) - 1, 20)):
            if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
                peaks.append((i, float(autocorr[i])))

        if peaks:
            # Most significant peak (excluding lag 0)
            peaks.sort(key=lambda x: x[1], reverse=True)
            period = peaks[0][0]
            strength = peaks[0][1] / autocorr[0] if autocorr[0] != 0 else 0

            return {
                "detected": True,
                "period": period,
                "strength": float(strength),
            }

        return {"detected": False}

    def get_realtime_summary(
        self, data: list[dict[str, Any]], fields: list[str]
    ) -> dict[str, Any]:
        """
        Get a real-time summary of key metrics

        Args:
            data: Recent data records
            fields: Fields to summarize

        Returns:
            Summary dictionary
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "record_count": len(data),
            "fields": {},
        }

        for field in fields:
            values = [
                record[field]
                for record in data
                if field in record and isinstance(record[field], (int, float))
            ]

            if values:
                summary["fields"][field] = {
                    "current": values[-1] if values else None,
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "trend": self._simple_trend(values),
                }

        return summary

    def _simple_trend(self, values: list[float]) -> str:
        """Calculate simple trend direction"""
        if len(values) < 2:
            return "unknown"

        recent = values[-min(5, len(values)) :]
        if len(recent) < 2:
            return "stable"

        slope = (recent[-1] - recent[0]) / len(recent)
        mean = np.mean(values)

        if abs(slope) < mean * 0.01:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
