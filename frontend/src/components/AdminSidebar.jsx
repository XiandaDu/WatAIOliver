import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from "@/components/ui/button"

export default function AdminSidebar({ title }) {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    {
      name: "Admin Panel",
      path: "/admin",
      icon: "📊"
    }
  ]

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-5 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Admin Dashboard</h2>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.path}>
              <Button
                variant={isActive(item.path) ? "default" : "ghost"}
                className={`w-full justify-start text-left ${
                  isActive(item.path)
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
                onClick={() => navigate(item.path)}
              >
                <span className="mr-3">{item.icon}</span>
                {item.name}
              </Button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="p-4 border-t border-gray-200">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => navigate('/')}
        >
          ← Back to Home
        </Button>
      </div>
    </div>
  )
} 