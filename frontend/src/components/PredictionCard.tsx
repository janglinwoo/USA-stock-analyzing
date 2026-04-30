import React from 'react';
import { Prediction } from '@types';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface Props {
  prediction: Prediction;
}

export const PredictionCard: React.FC<Props> = ({ prediction }) => {
  const isUptrend = prediction.direction_prediction === 1;
  const confidence = (prediction.direction_confidence * 100).toFixed(1);
  const priceChange = prediction.predicted_price_change.toFixed(2);
  const sentimentScore = prediction.combined_sentiment.toFixed(2);

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-green-600';
    if (score < -0.3) return 'text-red-600';
    return 'text-gray-600';
  };

  const getMomentumColor = (score: number) => {
    if (score > 0.5) return 'bg-green-100 text-green-800';
    if (score < -0.5) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{prediction.ticker}</h3>
          <p className="text-sm text-gray-500">
            {new Date(prediction.prediction_date).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isUptrend ? (
            <TrendingUp className="w-6 h-6 text-green-600" />
          ) : (
            <TrendingDown className="w-6 h-6 text-red-600" />
          )}
        </div>
      </div>

      {/* Direction & Confidence */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Direction</span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              isUptrend
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {isUptrend ? '📈 UP' : '📉 DOWN'}
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              isUptrend ? 'bg-green-600' : 'bg-red-600'
            }`}
            style={{ width: `${Math.min(confidence as any, 100)}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-600 mt-1">Confidence: {confidence}%</p>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-600 uppercase">Current Price</p>
          <p className="text-lg font-semibold text-gray-900">
            ${prediction.current_price.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase">Expected Change</p>
          <p
            className={`text-lg font-semibold ${
              parseFloat(priceChange) > 0
                ? 'text-green-600'
                : 'text-red-600'
            }`}
          >
            {parseFloat(priceChange) > 0 ? '+' : ''}{priceChange}%
          </p>
        </div>
      </div>

      {/* Price Range */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <p className="text-xs text-gray-600 uppercase mb-2">Price Range</p>
        <div className="flex items-center justify-between text-sm">
          <span className="text-red-600">
            ${prediction.predicted_price_range_low.toFixed(2)}
          </span>
          <div className="flex-1 mx-2 bg-gradient-to-r from-red-200 to-green-200 h-2 rounded"></div>
          <span className="text-green-600">
            ${prediction.predicted_price_range_high.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Sentiment & Momentum */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-600 uppercase mb-1">Sentiment</p>
          <p className={`text-lg font-semibold ${getSentimentColor(parseFloat(sentimentScore))}`}>
            {sentimentScore}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase mb-1">Momentum</p>
          <div className={`px-2 py-1 rounded text-xs font-semibold ${getMomentumColor(prediction.momentum_score)}`}>
            {prediction.momentum_score.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
};
