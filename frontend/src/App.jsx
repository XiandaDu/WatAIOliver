import { Routes, Route } from "react-router-dom"
import Home from "./pages/Home.jsx"
import ChatPage from "./pages/Chat.jsx"
import AdminPage from "./pages/Admin.jsx"
import EditAdminEntry from "./pages/EditAdminEntry.jsx"
import Log from "./pages/Log.jsx"
import Login from "./pages/Login.jsx"
import CourseSelection from "./pages/CourseSelection.jsx"

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/home" element={<Home />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/admin/edit" element={<EditAdminEntry />} />
      <Route path="/admin/logs" element={<Log />} />
      <Route path="/courses" element={<CourseSelection />} />
      <Route path="/" element={<Login />} />
    </Routes>
  )
}

export default App
