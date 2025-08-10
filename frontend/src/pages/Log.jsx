import React, { useEffect, useMemo, useState } from "react";
import AdminSidebar from "../components/AdminSidebar";
import { Bar, Doughnut } from "react-chartjs-2";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

export default function Log() {
  const [analytics, setAnalytics] = useState(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const courseId = params.get('course_id');
    if (!courseId) return;
    fetch(`http://localhost:8000/messages/analytics/course/${encodeURIComponent(courseId)}`)
      .then(r => r.json())
      .then(setAnalytics)
      .catch(() => setAnalytics(null));
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
          <h1 className="text-2xl font-bold text-gray-900">View Logs</h1>
        </header>
        {/* Main Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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

          {analytics && analytics.recent_pairs && (
            <div className="bg-white rounded-lg shadow p-6 mt-8">
              <h2 className="text-xl font-semibold mb-4">Recent Q&A (Anonymized)</h2>
              <ul className="space-y-4">
                {analytics.recent_pairs.map((p, idx) => (
                  <li key={idx} className="border rounded p-4">
                    <div className="text-gray-800 font-medium mb-2">Student</div>
                    <div className="text-gray-700 whitespace-pre-wrap mb-3">{p.user}</div>
                    <div className="text-gray-800 font-medium mb-2">Assistant</div>
                    <div className="text-gray-700 whitespace-pre-wrap">{p.assistant}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
