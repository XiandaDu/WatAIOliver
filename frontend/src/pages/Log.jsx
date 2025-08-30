import React, { useEffect, useMemo, useState } from "react";
import AdminSidebar from "../components/AdminSidebar";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import { Chart, registerables } from "chart.js";
import { MessageTimeline, MessageStats } from "../components/ui/message-timeline";
Chart.register(...registerables);

export default function Log() {
  const [analytics, setAnalytics] = useState(null);
  const [messages, setMessages] = useState([]);
  const [courseId, setCourseId] = useState(null);
  const [viewMode, setViewMode] = useState('timeline'); // 'timeline' or 'analytics'

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('course_id');
    if (!id) return;
    setCourseId(id);
    
    // Load analytics
    fetch(`http://localhost:8000/messages/analytics/course/${encodeURIComponent(id)}`)
      .then(r => r.json())
      .then(setAnalytics)
      .catch(() => setAnalytics(null));
    
    // Load raw messages for timeline
    fetch(`http://localhost:8000/messages/course/${encodeURIComponent(id)}`)
      .then(r => r.json())
      .then(setMessages)
      .catch(() => setMessages([]));
  }, []);

  const usageData = useMemo(() => {
    if (!analytics) return { labels: [], datasets: [] };
    return {
      labels: analytics.usage_by_day.labels,
      datasets: [
        {
          label: "Messages",
          data: analytics.usage_by_day.counts,
          backgroundColor: "rgba(54, 162, 235, 0.5)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
      ],
    };
  }, [analytics]);

  const conversationsByModel = useMemo(() => {
    if (!analytics) return { labels: [], datasets: [] };
    const labels = Object.keys(analytics.conversations_by_model || {});
    const values = Object.values(analytics.conversations_by_model || {});
    return {
      labels,
      datasets: [
        {
          label: "Assistant Messages by Model",
          data: values,
          backgroundColor: ["#3b82f6", "#f59e42", "#10b981", "#ef4444"],
          borderColor: ["#2563eb", "#ea580c", "#059669", "#b91c1c"],
          borderWidth: 1,
        },
      ],
    };
  }, [analytics]);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="px-8 py-6 border-b bg-white flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Course Analytics</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'timeline' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Timeline View
            </button>
            <button
              onClick={() => setViewMode('analytics')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'analytics' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Analytics View
            </button>
          </div>
        </header>
        {/* Main Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {viewMode === 'timeline' ? (
            <div className="space-y-6">
              <MessageStats messages={messages} />
              <MessageTimeline messages={messages} />
            </div>
          ) : (
            <div className="space-y-8">
              {analytics && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
                    <span className="text-3xl font-bold text-blue-600">{analytics.total_conversations}</span>
                    <span className="text-gray-500 mt-2">Total Conversations</span>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
                    <span className="text-3xl font-bold text-green-600">{analytics.active_users}</span>
                    <span className="text-gray-500 mt-2">Active Users</span>
                  </div>
                </div>
              )}
              
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Usage Patterns</h2>
                <div className="flex flex-col md:flex-row gap-8">
                  <div className="w-full md:w-1/2 h-80 flex flex-col items-center justify-center">
                    <Bar
                      data={usageData}
                      options={{
                        responsive: true,
                        plugins: {
                          legend: { position: "top" },
                        },
                        scales: {
                          y: { beginAtZero: true },
                        },
                      }}
                    />
                    <span className="mt-2 text-sm text-gray-500">Conversations by Day</span>
                  </div>
                  <div className="w-full md:w-1/2 h-80 flex flex-col items-center justify-center">
                    <Doughnut
                      data={conversationsByModel}
                      options={{
                        responsive: true,
                        plugins: {
                          legend: { position: "top" },
                        },
                      }}
                    />
                    <span className="mt-2 text-sm text-gray-500">Conversations by Model</span>
                  </div>
                </div>
              </div>


            </div>
          )}
        </main>
      </div>
    </div>
  );
}
