import React, { useState, useEffect } from 'react';
import { WritingStats, getWritingStats, getDailyStats, getWritingStreak, DailyStat } from '../api/writing';

interface WritingStatsPanelProps {
  taskId: number;
}

export const WritingStatsPanel: React.FC<WritingStatsPanelProps> = ({ taskId }) => {
  const [stats, setStats] = useState<WritingStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [streak, setStreak] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [taskId]);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const [statsData, dailyData, streakData] = await Promise.all([
        getWritingStats(taskId),
        getDailyStats(taskId, 30),
        getWritingStreak(taskId),
      ]);
      setStats(statsData);
      setDailyStats(dailyData);
      setStreak(streakData.streak);
    } catch (error) {
      console.error('Failed to load writing stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="writing-stats-panel p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="writing-stats-panel p-4">
        <div className="text-center text-gray-500">暂无统计数据</div>
      </div>
    );
  }

  // 计算热力图数据
  const maxWords = Math.max(...dailyStats.map((d) => d.words), 1);
  const today = new Date();
  const heatmapData = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(today);
    date.setDate(date.getDate() - (29 - i));
    const dateStr = date.toISOString().split('T')[0];
    const stat = dailyStats.find((d) => d.date === dateStr);
    return {
      date: dateStr,
      words: stat?.words || 0,
      intensity: stat ? Math.min(Math.ceil((stat.words / maxWords) * 4), 4) : 0,
    };
  });

  return (
    <div className="writing-stats-panel">
      <h3 className="text-lg font-semibold mb-4">写作统计</h3>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.today_words.toLocaleString()}</div>
          <div className="text-xs text-blue-500">今日字数</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{stats.week_words.toLocaleString()}</div>
          <div className="text-xs text-green-500">本周字数</div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{streak}</div>
          <div className="text-xs text-purple-500">连续天数</div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{stats.avg_speed}</div>
          <div className="text-xs text-orange-500">字/小时</div>
        </div>
      </div>

      {/* 总字数 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">总字数</span>
          <span className="text-lg font-semibold">{stats.total_words.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">写作天数</span>
          <span className="text-lg font-semibold">{stats.writing_days}</span>
        </div>
      </div>

      {/* 热力图 */}
      <div>
        <h4 className="text-sm font-medium mb-2">近30天写作量</h4>
        <div className="flex flex-wrap gap-1">
          {heatmapData.map((day, index) => (
            <div
              key={index}
              className="w-3 h-3 rounded-sm cursor-pointer"
              style={{
                backgroundColor:
                  day.intensity === 0
                    ? '#f3f4f6'
                    : day.intensity === 1
                    ? '#dbeafe'
                    : day.intensity === 2
                    ? '#93c5fd'
                    : day.intensity === 3
                    ? '#3b82f6'
                    : '#1d4ed8',
              }}
              title={`${day.date}: ${day.words} 字`}
            />
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>30天前</span>
          <span>今天</span>
        </div>
      </div>

      {/* 刷新按钮 */}
      <button
        onClick={loadStats}
        className="mt-4 w-full text-xs text-gray-500 hover:text-gray-700 py-1"
      >
        刷新统计
      </button>
    </div>
  );
};

export default WritingStatsPanel;
