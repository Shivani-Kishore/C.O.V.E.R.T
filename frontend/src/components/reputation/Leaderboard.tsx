import React, { useState, useEffect } from 'react';
import { ReputationBadge } from './ReputationBadge';

interface LeaderboardEntry {
  rank: number;
  wallet_address: string;
  reputation_score: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  total_reviews: number;
  accuracy_rate: number;
}

interface LeaderboardProps {
  className?: string;
}

export function Leaderboard({ className = '' }: LeaderboardProps) {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchLeaderboard();
  }, [filter]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter) {
        params.append('tier', filter);
      }

      const response = await fetch(`/api/v1/reputation/leaderboard?${params}`);
      const data = await response.json();
      setLeaderboard(data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-900">Moderator Leaderboard</h2>
        <p className="text-sm text-gray-600 mt-1">
          Top moderators by reputation score
        </p>

        <div className="flex space-x-2 mt-4">
          <button
            onClick={() => setFilter(null)}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              filter === null
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          {['bronze', 'silver', 'gold', 'platinum'].map((tier) => (
            <button
              key={tier}
              onClick={() => setFilter(tier)}
              className={`px-3 py-1 rounded-md text-sm font-medium capitalize ${
                filter === tier
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : leaderboard.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No moderators found</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Moderator
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reviews
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Accuracy
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leaderboard.map((entry) => (
                <tr key={entry.rank} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {entry.rank <= 3 && (
                        <span className="text-sm font-bold mr-2 text-indigo-600">
                          {entry.rank === 1 ? '1st' : entry.rank === 2 ? '2nd' : '3rd'}
                        </span>
                      )}
                      <span className="text-sm font-medium text-gray-900">
                        #{entry.rank}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-mono text-gray-900">
                      {entry.wallet_address}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <ReputationBadge
                      tier={entry.tier}
                      score={entry.reputation_score}
                      size="sm"
                      showScore={false}
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-gray-900">
                      {entry.reputation_score}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{entry.total_reviews}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-green-600">
                      {entry.accuracy_rate.toFixed(1)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
