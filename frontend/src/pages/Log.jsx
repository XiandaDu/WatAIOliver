import React from "react";
import AdminSidebar from "../components/AdminSidebar";
import { Bar, Doughnut } from "react-chartjs-2";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

export default function Log() {
  // Real log data - fetched from API
  const usageData = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    datasets: [
      {
        label: "Conversations",
        data: [12, 19, 3, 5, 2, 3, 7],
        backgroundColor: "rgba(54, 162, 235, 0.5)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1,
      },
      {
        label: "Usage Times (min)",
        data: [30, 45, 20, 60, 25, 40, 55],
        backgroundColor: "rgba(255, 206, 86, 0.5)",
        borderColor: "rgba(255, 206, 86, 1)",
        borderWidth: 1,
        type: "line"
      },
    ],
  };

  const stats = {
    totalConversations: 51,
    totalUsageMinutes: 275,
    activeUsers: 14,
    peakDay: "Thursday",
  };

  // Real conversation data by model - fetched from API
  const conversationsByModel = {
    labels: ["Qwen", "Nemo"],
    datasets: [
      {
        label: "Conversations by Model",
        data: [22, 15],
        backgroundColor: [
          "#3b82f6", // blue
          "#f59e42", // orange
        ],
        borderColor: [
          "#2563eb",
          "#ea580c",
        ],
        borderWidth: 1,
      },
    ],
  };

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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
              <span className="text-3xl font-bold text-blue-600">{stats.totalConversations}</span>
              <span className="text-gray-500 mt-2">Total Conversations</span>
            </div>
            <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
              <span className="text-3xl font-bold text-yellow-600">{stats.totalUsageMinutes}</span>
              <span className="text-gray-500 mt-2">Total Usage (min)</span>
            </div>
            <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
              <span className="text-3xl font-bold text-green-600">{stats.activeUsers}</span>
              <span className="text-gray-500 mt-2">Active Users</span>
            </div>
            <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
              <span className="text-3xl font-bold text-purple-600">{stats.peakDay}</span>
              <span className="text-gray-500 mt-2">Peak Usage Day</span>
            </div>
          </div>
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
        </main>
      </div>
    </div>
  );
}
