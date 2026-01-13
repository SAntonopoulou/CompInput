import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import PledgeForm from '../components/PledgeForm';
import RateVideo from '../components/RateVideo';

const ProjectDetail = () => {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await client.get(`/projects/${id}`);
        setProject(response.data);
        
        // Fetch videos if project has them
        if (response.data.status === 'in_progress' || response.data.status === 'completed') {
            const videosRes = await client.get('/videos/', { params: { project_id: id } });
            setVideos(videosRes.data);
        }
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
                {project.requester_name ? (
                    <>Requested by <Link to={`/profile/${project.requester_id}`} className="text-indigo-600 hover:underline">{project.requester_name}</Link></>
                ) : (
                    <>By <Link to={`/profile/${project.teacher_id}`} className="text-indigo-600 hover:underline">{project.teacher_name}</Link></>
                )}
            </span>
          </div>

          <div className="prose prose-indigo max-w-none text-gray-500 mb-8">
            <p className="whitespace-pre-line">{project.description}</p>
          </div>

          {/* Videos Section */}
          {videos.length > 0 && (
              <div className="mt-8 border-t border-gray-200 pt-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Project Videos</h2>
                  <div className="space-y-6">
                      {videos.map(video => (
                          <div key={video.id} className="bg-white p-4 rounded-lg shadow border border-gray-200">
                              <h3 className="text-lg font-medium text-gray-900">{video.title}</h3>
                              <div className="aspect-w-16 aspect-h-9 mt-2 mb-4 bg-gray-100 rounded flex items-center justify-center">
                                  {/* Placeholder for video embed */}
                                  <a href={video.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center">
                                      <svg className="h-8 w-8 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" /></svg>
                                      Watch on {video.platform}
                                  </a>
                              </div>
                              {token && <RateVideo videoId={video.id} />}
                          </div>
                      ))}
                  </div>
              </div>
          )}
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
             {project.delivery_days && !project.deadline && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-sm text-gray-500">
                        Delivery: {project.delivery_days} days after funding
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
