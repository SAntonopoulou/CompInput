import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import RequestList from './pages/RequestList';
import TeacherRoute from './components/TeacherRoute';
import Dashboard from './pages/teacher/Dashboard';
import CreateProject from './pages/teacher/CreateProject';
import EditProject from './pages/teacher/EditProject';
import StudentDashboard from './pages/student/Dashboard';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Landing from './pages/Landing';

function App() {
  const token = localStorage.getItem('token');

  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-gray-100">
          <Navbar />
          <Routes>
            <Route path="/" element={token ? <ProjectList /> : <Landing />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/requests" element={<RequestList />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile/:id" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            
            {/* Student Routes */}
            <Route path="/student/dashboard" element={<StudentDashboard />} />
            
            {/* Teacher Routes */}
            <Route element={<TeacherRoute />}>
              <Route path="/teacher/dashboard" element={<Dashboard />} />
              <Route path="/teacher/create-project" element={<CreateProject />} />
              <Route path="/teacher/projects/:id/edit" element={<EditProject />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </ToastProvider>
  );
}

export default App;
