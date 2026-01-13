import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import PledgeForm from '../components/PledgeForm';

const ProjectDetail = () => {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await client.get(`/projects/${id}`);
        setProject(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to load project details.");
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [id]);

  if (loading) return <div className="text-center py-10">Loading...</div>;
  if (error) return <div className="text-center py-10 text-red-600">{error}</div>;
  if (!project) return <div className="text-center py-10">Project not found</div>;

  const percentage = Math.min(
    (project.current_amount / project.goal_amount) * 100,
    100
  );

  const formatCurrency = (amountInCents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amountInCents / 100);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="lg:grid lg:grid-cols-3 lg:gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl mb-4">
            {project.title}
          </h1>
          
          <div className="flex items-center space-x-4 mb-6">
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {project.language}
            </span>
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
              {project.level}
            </span>
            <span className="text-gray-500 text-sm">
                By {project.teacher_name}
            </span>
          </div>

          <div className="prose prose-indigo max-w-none text-gray-500">
            <p className="whitespace-pre-line">{project.description}</p>
          </div>
        </div>

        {/* Sidebar / Action Area */}
        <div className="mt-8 lg:mt-0">
          <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200 sticky top-6">
            <div className="mb-6">
              <div className="flex justify-between text-base font-medium text-gray-900 mb-1">
                <span>{formatCurrency(project.current_amount)}</span>
                <span className="text-gray-500">goal {formatCurrency(project.goal_amount)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
              <p className="mt-2 text-sm text-gray-500 text-right">
                  {Math.round(percentage)}% funded
              </p>
            </div>

            {project.status === 'active' || project.status === 'funded' ? (
                token ? (
                    <PledgeForm projectId={project.id} projectName={project.title} />
                ) : (
                    <div className="text-center">
                        <p className="text-gray-600 mb-4">Log in to back this project.</p>
                        <Link
                            to="/login"
                            className="block w-full bg-indigo-600 text-white text-center py-2 px-4 rounded-md hover:bg-indigo-700"
                        >
                            Login to Pledge
                        </Link>
                    </div>
                )
            ) : (
                <div className="bg-gray-100 p-4 rounded text-center text-gray-600">
                    This project is {project.status.replace('_', ' ')}.
                </div>
            )}
            
            {project.deadline && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-sm text-gray-500">
                        Deadline: {new Date(project.deadline).toLocaleDateString()}
                    </p>
                </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;
