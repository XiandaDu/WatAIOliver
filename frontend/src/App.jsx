import { Routes, Route } from "react-router-dom"
import ChatPage from "./pages/Chat.jsx"
import AdminPage from "./pages/Admin.jsx"

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="/admin" element={<AdminPage />} />
    </Routes>
  )
}

export default App
