import React from 'react';
import { ReputationBadge } from './ReputationBadge';

interface ReputationCardProps {
  reputation: {
    reputation_score: number;
    tier: 'bronze' | 'silver' | 'gold' | 'platinum';
    total_reviews: number;
    accurate_reviews: number;
    disputed_reviews: number;
    accuracy_rate: number;
    daily_rate_limit: number;
  };
  className?: string;
}

export function ReputationCard({ reputation, className = '' }: ReputationCardProps) {
  const tierThresholds = {
    bronze: 0,
    silver: 100,
    gold: 500,
    platinum: 1000,
  };

  const nextTierThreshold =
    reputation.tier === 'platinum'
      ? null
      : reputation.tier === 'gold'
      ? tierThresholds.platinum
      : reputation.tier === 'silver'
      ? tierThresholds.gold
      : tierThresholds.silver;

  const progress = nextTierThreshold
    ? ((reputation.reputation_score - tierThresholds[reputation.tier]) /
        (nextTierThreshold - tierThresholds[reputation.tier])) *
      100
    : 100;

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Your Reputation</h3>
        <ReputationBadge
          tier={reputation.tier}
          score={reputation.reputation_score}
          size="md"
        />
      </div>

      {nextTierThreshold && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress to next tier</span>
            <span>
              {reputation.reputation_score} / {nextTierThreshold}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-2xl font-bold text-gray-900">
            {reputation.total_reviews}
          </div>
          <div className="text-sm text-gray-600">Total Reviews</div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-2xl font-bold text-green-600">
            {reputation.accuracy_rate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Accuracy Rate</div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-2xl font-bold text-blue-600">
            {reputation.accurate_reviews}
          </div>
          <div className="text-sm text-gray-600">Accurate Reviews</div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-2xl font-bold text-red-600">
            {reputation.disputed_reviews}
          </div>
          <div className="text-sm text-gray-600">Disputed Reviews</div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Daily Review Limit</span>
          <span className="font-semibold text-gray-900">
            {reputation.daily_rate_limit} reports/day
          </span>
        </div>
      </div>
    </div>
  );
}
