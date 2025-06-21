import { useNavigate } from 'react-router-dom'
import { Button } from "@/components/ui/button"

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-white to-gray-100">
      <div className="text-center space-y-6 p-8">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          Welcome to Oliver
        </h1>
        <p className="text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
          Your intelligent education assistant.
        </p>
        <div className="mt-10 space-y-4">
          <Button 
            size="lg"
            onClick={() => navigate('/chat')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
          >
            Start Chatting
          </Button>
          <div className="pt-2">
            <Button 
              variant="outline"
              size="lg"
              onClick={() => navigate('/admin')}
              className="border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 px-8 py-6 text-lg"
            >
              Admin Panel
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
