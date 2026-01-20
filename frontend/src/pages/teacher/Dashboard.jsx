import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import client from '../../api/client';
import LinkVideoModal from '../../components/VideoUpload';
import ConfirmationModal from '../../components/ConfirmationModal';
import { useToast } from '../../context/ToastContext';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState({});
  
  const { addToast } = useToast();
  const location = useLocation();

  const fetchData = async () => {
    try {
      const userRes = await client.get('/users/me');
      setUser(userRes.data);
      
      const projectsRes = await client.get('/projects/me');
      // Filter out cancelled projects from the main view
      const activeProjects = projectsRes.data.filter(p => p.status !== 'cancelled');
      setProjects(activeProjects);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
      addToast("Failed to load dashboard data", 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Check for redirect from Stripe onboarding
    const queryParams = new URLSearchParams(location.search);
    if (queryParams.get('stripe_return') === 'true') {
      addToast("Stripe account connected! Your status will update shortly.", 'info');
      // Refetch data after a delay to allow webhook to process
      const timer = setTimeout(() => {
        fetchData();
      }, 3000); // 3-second delay
      return () => clearTimeout(timer);
    }
  }, [addToast, location.search]);

  const handleSetupPayouts = async () => {
    try {
      const response = await client.post('/users/stripe-onboarding-link');
      window.location.href = response.data.onboarding_url;
    } catch (error) {
      console.error("Failed to setup payouts", error);
      addToast("Failed to initiate Stripe onboarding.", 'error');
    }
  };

  const handleLinkVideo = (projectId) => {
    setSelectedProjectId(projectId);
    setShowVideoModal(true);
  };

  const handleVideoLinkSuccess = () => {
    setShowVideoModal(false);
    addToast("Video linked successfully!", 'success');
    // Refresh projects
    client.get('/projects/me').then(res => {
        const activeProjects = res.data.filter(p => p.status !== 'cancelled');
        setProjects(activeProjects);
    });
  };

  const confirmRequestCompletion = (projectId) => {
    setModalConfig({
      title: "Request Completion",
      message: "Are you sure? This will notify all backers to confirm the project is complete.",
      confirmText: "Request Confirmation",
      isDanger: false,
      onConfirm: () => handleRequestCompletion(projectId)
    });
    setModalOpen(true);
  };

  const handleRequestCompletion = async (projectId) => {
    setModalOpen(false);
    try {
      await client.post(`/projects/${projectId}/complete`);
      // Refresh projects
      const res = await client.get('/projects/me');
      const activeProjects = res.data.filter(p => p.status !== 'cancelled');
      setProjects(activeProjects);
      addToast("Confirmation requested from students. You will be notified when the project is confirmed and funds are released.", 'success');
    } catch (error) {
      console.error("Failed to request completion", error);
      addToast(error.response?.data?.detail || "Failed to request completion.", 'error');
    }
  };

  const confirmCancelProject = (projectId) => {
    setModalConfig({
      title: "Cancel Project",
      message: "Are you sure? This will refund all backers and cannot be undone.",
      confirmText: "Cancel Project",
      isDanger: true,
      onConfirm: () => handleCancelProject(projectId)
    });
    setModalOpen(true);
  };

  const handleCancelProject = async (projectId) => {
      setModalOpen(false);
      try {
          await client.post(`/projects/${projectId}/cancel`);
          const res = await client.get('/projects/me');
          const activeProjects = res.data.filter(p => p.status !== 'cancelled');
          setProjects(activeProjects);
          addToast("Project cancelled and refunds initiated.", 'success');
      } catch (error) {
          console.error("Failed to cancel project", error);
          addToast(error.response?.data?.detail || "Failed to cancel project.", 'error');
      }
  };

  if (loading) return <div className="p-10 text-center">Loading dashboard...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h1>
        <Link
          to="/teacher/create-project"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
        >
          Create New Project
        </Link>
      </div>

      {/* Stripe Status */}
      {!user?.stripe_account_id && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8">
          <div className="flex">
            <div className="flex-shrink-0">
              {/* Icon */}
              <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                You need to setup payouts to receive funds.
                <button
                  onClick={handleSetupPayouts}
                  className="ml-2 font-medium underline hover:text-yellow-600 focus:outline-none"
                >
                  Setup Payouts
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Projects List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {projects.length === 0 ? (
            <li className="px-4 py-4 sm:px-6 text-center text-gray-500">
              No active projects. Create one to get started!
            </li>
          ) : (
            projects.map((project) => (
              <li key={project.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                        <p className="text-sm font-medium text-indigo-600 truncate">{project.title}</p>
                        <p className="text-xs text-gray-500">Status: {project.status}</p>
                    </div>
                    <div className="ml-2 flex-shrink-0 flex space-x-2">
                      {project.status === 'draft' && (
                        <Link
                          to={`/teacher/projects/${project.id}/edit`}
                          className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800 hover:bg-gray-200"
                        >
                          Edit
                        </Link>
                      )}
                      
                      {project.status === 'successful' && (
                        <button
                          onClick={() => handleLinkVideo(project.id)}
                          className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 hover:bg-blue-200"
                        >
                          Link Video
                        </button>
                      )}

                      {project.status === 'successful' && (
                        <button
                          onClick={() => confirmRequestCompletion(project.id)}
                          className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 hover:bg-green-200"
                        >
                          Request Completion
                        </button>
                      )}

                      {project.status !== 'completed' && project.status !== 'cancelled' && (
                          <button
                            onClick={() => confirmCancelProject(project.id)}
                            className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 hover:bg-red-200"
                          >
                              Cancel
                          </button>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        Goal: ${(project.funding_goal / 100).toFixed(2)}
                      </p>
                      <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                        Raised: ${(project.current_funding / 100).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Video Upload Modal */}
      {showVideoModal && (
        <LinkVideoModal
            projectId={selectedProjectId} 
            onClose={() => setShowVideoModal(false)}
            onSuccess={handleVideoLinkSuccess}
        />
      )}

      {/* Confirmation Modal */}
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

export default Dashboard;
