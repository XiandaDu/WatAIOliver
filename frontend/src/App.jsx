import { Routes, Route } from "react-router-dom"
import Home from "./pages/Home.jsx"
import ChatPage from "./pages/Chat.jsx"
import AdminPage from "./pages/Admin.jsx"
import EditAdminEntry from "./pages/EditAdminEntry.jsx"
import Log from "./pages/Log.jsx"
import Login from "./pages/Login.jsx"

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/home" element={<Home />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/admin/edit" element={<EditAdminEntry />} />
      <Route path="/admin/logs" element={<Log />} />
      <Route path="/" element={<Login />} />
    </Routes>
  )
}

export default App
