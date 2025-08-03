import React, { useState, useEffect } from "react";
import AdminSidebar from "../components/AdminSidebar";
import { Bar, Doughnut } from "react-chartjs-2";
import { Chart, registerables } from "chart.js";
import { adminAPI } from "../lib/api";
import { conversationAPI } from "../lib/api";
Chart.register(...registerables);

export default function Log() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({
    totalConversations: 0,
    totalUsageMinutes: 0,
    activeUsers: 0,
    peakDay: "-",
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch conversations
        const convoResponse = await conversationAPI.getConversations();
        if (convoResponse.success) {
          setConversations(convoResponse.data);
        }

        // Fetch messages
        const msgResponse = await adminAPI.getAllMessages();
        if (msgResponse.success) {
          setMessages(msgResponse.data);
        }

        // Fetch users
        const userResponse = await adminAPI.getAllUsers();
        if (userResponse.success) {
          setUsers(userResponse.data);
        }

        // Calculate stats
        const totalConvos = convoResponse.success ? convoResponse.data.length : 0;
        const activeUsers = userResponse.success ? userResponse.data.filter(u => u.last_login_at).length : 0;
        
        setStats({
          totalConversations: totalConvos,
          totalUsageMinutes: Math.round(msgResponse.success ? msgResponse.data.length * 0.5 : 0), // Rough estimate
          activeUsers: activeUsers,
          peakDay: getPeakUsageDay(convoResponse.data),
        });

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Helper function to get peak usage day
  const getPeakUsageDay = (conversations) => {
    if (!conversations?.length) return "-";
    const dayCounts = {};
    conversations.forEach(conv => {
      const day = new Date(conv.created_at).toLocaleDateString('en-US', { weekday: 'long' });
      dayCounts[day] = (dayCounts[day] || 0) + 1;
    });
    return Object.entries(dayCounts).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  };

  // Prepare chart data
  const usageData = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    datasets: [
      {
        label: "Conversations",
        data: conversations.reduce((acc, conv) => {
          const day = new Date(conv.created_at).getDay();
          acc[day === 0 ? 6 : day - 1]++;
          return acc;
        }, Array(7).fill(0)),
        backgroundColor: "rgba(54, 162, 235, 0.5)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1,
      },
      {
        label: "Messages",
        data: messages.reduce((acc, msg) => {
          const day = new Date(msg.created_at).getDay();
          acc[day === 0 ? 6 : day - 1]++;
          return acc;
        }, Array(7).fill(0)),
        backgroundColor: "rgba(255, 206, 86, 0.5)",
        borderColor: "rgba(255, 206, 86, 1)",
        borderWidth: 1,
        type: "line"
      },
    ],
  };

  const conversationsByModel = {
    labels: ["Qwen", "Nemo"],
    datasets: [
      {
        label: "Conversations by Model",
        data: [
          conversations.filter(c => c.model === "qwen").length,
          conversations.filter(c => c.model === "nemo").length,
        ],
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
          {loading && (
            <span className="text-sm text-gray-500">Loading data...</span>
          )}
        </header>
        {/* Main Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
              <p className="text-red-600">Error: {error}</p>
            </div>
          ) : (
            <>
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

              <div className="bg-white rounded-lg shadow p-6 mb-8">
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
                    <span className="mt-2 text-sm text-gray-500">Activity by Day</span>
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

              {/* Data Tables */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Users Table */}
                <div className="bg-white rounded-lg shadow">
                  <div className="p-6 border-b">
                    <h2 className="text-xl font-semibold">Users</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Active</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user, i) => (
                          <tr key={user.id || i}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.email}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.last_login_at ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                              }`}>
                                {user.last_login_at ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Conversations Table */}
                <div className="bg-white rounded-lg shadow">
                  <div className="p-6 border-b">
                    <h2 className="text-xl font-semibold">Recent Conversations</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {conversations.slice(0, 10).map((conv, i) => (
                          <tr key={conv.id || i}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{conv.title}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{conv.model || 'Unknown'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(conv.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
