import { Routes, Route } from "react-router-dom"
import Home from "./pages/Home.jsx"
import ChatPage from "./pages/Chat.jsx"
import AdminPage from "./pages/Admin.jsx"
import EditAdminEntry from "./pages/EditAdminEntry.jsx"
import Log from "./pages/Log.jsx"
import Login from "./pages/Login.jsx"
import CourseSelection from "./pages/CourseSelection.jsx"
import ProtectedRoute from "./components/ProtectedRoute.jsx"

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/home" element={<Home />} />
      <Route path="/chat" element={
        <ProtectedRoute>
          <ChatPage />
        </ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute requiredRoles={['instructor', 'admin']}>
          <AdminPage />
        </ProtectedRoute>
      } />
      <Route path="/admin/edit" element={
        <ProtectedRoute requiredRoles={['instructor', 'admin']}>
          <EditAdminEntry />
        </ProtectedRoute>
      } />
      <Route path="/admin/logs" element={
        <ProtectedRoute requiredRoles={['instructor', 'admin']}>
          <Log />
        </ProtectedRoute>
      } />
      <Route path="/courses" element={
        <ProtectedRoute requiredRoles={['student']}>
          <CourseSelection />
        </ProtectedRoute>
      } />
      <Route path="/" element={<Login />} />
    </Routes>
  )
}

export default App
