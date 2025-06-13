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
        <div className="mt-10">
          <Button 
            size="lg"
            onClick={() => navigate('/chat')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
          >
            Start Chatting
          </Button>
        </div>
      </div>
    </div>
  )
}
