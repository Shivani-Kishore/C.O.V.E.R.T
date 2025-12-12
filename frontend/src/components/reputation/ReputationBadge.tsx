import React from 'react';

interface ReputationBadgeProps {
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
}

const tierConfig = {
  bronze: {
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: 'B',
    gradient: 'from-orange-400 to-orange-600',
  },
  silver: {
    color: 'bg-gray-100 text-gray-800 border-gray-300',
    icon: 'S',
    gradient: 'from-gray-300 to-gray-500',
  },
  gold: {
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: 'G',
    gradient: 'from-yellow-400 to-yellow-600',
  },
  platinum: {
    color: 'bg-purple-100 text-purple-800 border-purple-300',
    icon: 'P',
    gradient: 'from-purple-400 to-purple-600',
  },
};

const sizeConfig = {
  sm: {
    container: 'px-2 py-1 text-xs',
    icon: 'text-sm',
  },
  md: {
    container: 'px-3 py-1.5 text-sm',
    icon: 'text-base',
  },
  lg: {
    container: 'px-4 py-2 text-base',
    icon: 'text-lg',
  },
};

export function ReputationBadge({
  tier,
  score,
  size = 'md',
  showScore = true,
}: ReputationBadgeProps) {
  const config = tierConfig[tier];
  const sizing = sizeConfig[size];

  return (
    <div
      className={`inline-flex items-center space-x-2 rounded-full border ${config.color} ${sizing.container} font-medium`}
    >
      <span className={sizing.icon}>{config.icon}</span>
      <span className="capitalize">{tier}</span>
      {showScore && <span className="font-bold">({score})</span>}
    </div>
  );
}
