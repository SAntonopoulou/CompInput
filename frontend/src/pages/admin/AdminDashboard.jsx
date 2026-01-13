import React, { useState, useEffect } from 'react';
import client from '../../api/client';
import ConfirmationModal from '../../components/ConfirmationModal';
import { useToast } from '../../context/ToastContext';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState({});
  
  const { addToast } = useToast();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await client.get('/admin/stats');
        setStats(statsRes.data);
        
        const usersRes = await client.get('/admin/users');
        setUsers(usersRes.data);

        // Fetch all projects (using the public list endpoint for now, might need a dedicated admin list if we want to see drafts/cancelled)
        // For admin purposes, let's just fetch public ones or add an admin param to list_projects later.
        // Re-using public list for simplicity, but filtering client side if needed.
        const projectsRes = await client.get('/projects/'); 
        setProjects(projectsRes.data);

      } catch (error) {
        console.error("Failed to fetch admin data", error);
        addToast("Failed to load admin dashboard", 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [addToast]);

  const confirmDeleteUser = (userId) => {
    setModalConfig({
      title: "Delete User",
      message: "Are you sure? This will anonymize their data and remove their login access.",
      confirmText: "Delete User",
      isDanger: true,
      onConfirm: () => handleDeleteUser(userId)
    });
    setModalOpen(true);
  };

  const handleDeleteUser = async (userId) => {
      setModalOpen(false);
      try {
          await client.delete(`/admin/users/${userId}`);
          setUsers(users.filter(u => u.id !== userId));
          addToast("User deleted successfully", 'success');
      } catch (error) {
          console.error("Failed to delete user", error);
          addToast("Failed to delete user", 'error');
      }
  };

  const confirmCancelProject = (projectId) => {
    setModalConfig({
      title: "Cancel Project",
      message: "Are you sure? This will refund all backers immediately.",
      confirmText: "Cancel Project",
      isDanger: true,
      onConfirm: () => handleCancelProject(projectId)
    });
    setModalOpen(true);
  };

  const handleCancelProject = async (projectId) => {
      setModalOpen(false);
      try {
          await client.delete(`/admin/projects/${projectId}`);
          // Refresh projects list
          const projectsRes = await client.get('/projects/');
          setProjects(projectsRes.data);
          addToast("Project cancelled successfully", 'success');
      } catch (error) {
          console.error("Failed to cancel project", error);
          addToast("Failed to cancel project", 'error');
      }
  };

  const formatCurrency = (amountInCents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amountInCents / 100);
  };

  if (loading) return <div className="p-10 text-center">Loading admin dashboard...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Users</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{stats?.user_count}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Projects</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{stats?.project_count}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Pledges</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{stats?.pledge_count}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Funds Raised</dt>
            <dd className="mt-1 text-3xl font-semibold text-green-600">{formatCurrency(stats?.total_funds_raised)}</dd>
          </div>
        </div>
      </div>

      {/* User Management */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Users</h2>
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {users.map((user) => (
              <li key={user.id} className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-indigo-600 truncate">{user.full_name}</p>
                  <p className="text-sm text-gray-500">{user.email} - <span className="capitalize">{user.role}</span></p>
                </div>
                {user.role !== 'admin' && (
                    <button
                    onClick={() => confirmDeleteUser(user.id)}
                    className="text-red-600 hover:text-red-900 text-sm font-medium"
                    >
                    Delete
                    </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Project Management */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Active Projects</h2>
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {projects.map((project) => (
              <li key={project.id} className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-indigo-600 truncate">{project.title}</p>
                  <p className="text-sm text-gray-500">by {project.teacher_name} - {project.status}</p>
                </div>
                <button
                  onClick={() => confirmCancelProject(project.id)}
                  className="text-red-600 hover:text-red-900 text-sm font-medium"
                >
                  Cancel
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <ConfirmationModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={modalConfig.onConfirm}
        title={modalConfig.title}
        message={modalConfig.message}
        confirmText={modalConfig.confirmText}
        isDanger={modalConfig.isDanger}
      />
    </div>
  );
};

export default AdminDashboard;
