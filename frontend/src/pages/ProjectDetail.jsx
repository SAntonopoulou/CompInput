import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import PledgeForm from '../components/PledgeForm';
import RateVideo from '../components/RateVideo';
import { useToast } from '../context/ToastContext';
import ProjectCard from '../components/ProjectCard';
import { getVideoThumbnail } from '../utils/video';

const ProjectDetail = () => {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [videos, setVideos] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [relatedProjects, setRelatedProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [newUpdate, setNewUpdate] = useState('');
  const [expandedVideoComments, setExpandedVideoComments] = useState({});
  const [videoComments, setVideoComments] = useState({});
  const [newComment, setNewComment] = useState({});
  
  const { addToast } = useToast();
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Project
        const response = await client.get(`/projects/${id}`);
        setProject(response.data);
        
        // Fetch User
        if (token) {
            try {
                const userRes = await client.get('/users/me');
                setCurrentUser(userRes.data);
            } catch (e) {
                console.error("Failed to fetch user");
            }
        }

        // Fetch Updates
        const updatesRes = await client.get(`/projects/${id}/updates`);
        setUpdates(updatesRes.data);
        
        // Fetch Videos if applicable
        if (response.data.status === 'in_progress' || response.data.status === 'completed') {
            const videosRes = await client.get('/videos/', { params: { project_id: id } });
            setVideos(videosRes.data);
        }

        // Fetch Related Projects
        const relatedRes = await client.get(`/projects/${id}/related`);
        setRelatedProjects(relatedRes.data);

      } catch (err) {
        console.error(err);
        setError("Failed to load project details.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, token]);

  const handlePostUpdate = async () => {
      if (!newUpdate.trim()) return;
      try {
          const res = await client.post(`/projects/${id}/updates`, { content: newUpdate });
          setUpdates([res.data, ...updates]);
          setNewUpdate('');
          addToast("Update posted!", 'success');
      } catch (error) {
          console.error("Failed to post update", error);
          addToast("Failed to post update", 'error');
      }
  };

  const toggleComments = async (videoId) => {
      if (expandedVideoComments[videoId]) {
          setExpandedVideoComments({ ...expandedVideoComments, [videoId]: false });
      } else {
          setExpandedVideoComments({ ...expandedVideoComments, [videoId]: true });
          if (!videoComments[videoId]) {
              try {
                  const res = await client.get(`/videos/${videoId}/comments`);
                  setVideoComments(prev => ({ ...prev, [videoId]: res.data }));
              } catch (error) {
                  console.error("Failed to load comments", error);
              }
          }
      }
  };

  const handlePostComment = async (videoId) => {
      const content = newComment[videoId];
      if (!content || !content.trim()) return;

      try {
          const res = await client.post(`/videos/${videoId}/comments`, { content });
          setVideoComments(prev => ({
              ...prev,
              [videoId]: [...(prev[videoId] || []), res.data]
          }));
          setNewComment({ ...newComment, [videoId]: '' });
      } catch (error) {
          console.error("Failed to post comment", error);
          addToast("Failed to post comment", 'error');
      }
  };

  if (loading) return <div className="text-center py-10">Loading...</div>;
  if (error) return <div className="text-center py-10 text-red-600">{error}</div>;
  if (!project) return <div className="text-center py-10">Project not found</div>;

  const percentage = Math.min(
    (project.current_funding / project.funding_goal) * 100,
    100
  );

  const formatCurrency = (amountInCents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amountInCents / 100);
  };

  const isOwner = currentUser && currentUser.id === project.teacher_id;
  const tags = project.tags ? project.tags.split(',').map(t => t.trim()) : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="lg:grid lg:grid-cols-3 lg:gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl mb-4">
            {project.title}
          </h1>
          
          <div className="flex flex-wrap items-center gap-2 mb-6">
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {project.language}
            </span>
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
              {project.level}
            </span>
            {tags.map((tag, index) => (
                <span key={index} className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                    {tag}
                </span>
            ))}
          </div>
          
          <div className="mb-6 text-gray-500 text-sm">
                {project.requester_name ? (
                    <>Requested by <Link to={`/profile/${project.requester_id}`} className="text-indigo-600 hover:underline">{project.requester_name}</Link></>
                ) : (
                    <>By <Link to={`/profile/${project.teacher_id}`} className="text-indigo-600 hover:underline">{project.teacher_name}</Link></>
                )}
          </div>

          <div className="prose prose-indigo max-w-none text-gray-500 mb-8">
            <p className="whitespace-pre-line">{project.description}</p>
          </div>

          {/* Project Updates */}
          <div className="mt-8 border-t border-gray-200 pt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Project Updates</h2>
              {isOwner && (
                  <div className="mb-6">
                      <textarea
                          className="w-full border border-gray-300 rounded-md p-2 text-sm"
                          rows={3}
                          placeholder="Post an update for your backers..."
                          value={newUpdate}
                          onChange={(e) => setNewUpdate(e.target.value)}
                      />
                      <div className="mt-2 text-right">
                          <button
                              onClick={handlePostUpdate}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
                          >
                              Post Update
                          </button>
                      </div>
                  </div>
              )}
              
              {updates.length === 0 ? (
                  <p className="text-gray-500 text-sm">No updates yet.</p>
              ) : (
                  <div className="space-y-4">
                      {updates.map(update => (
                          <div key={update.id} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                              <p className="text-gray-800 whitespace-pre-line">{update.content}</p>
                              <p className="text-xs text-gray-500 mt-2">{new Date(update.created_at).toLocaleDateString()}</p>
                          </div>
                      ))}
                  </div>
              )}
          </div>

          {/* Videos Section */}
          {videos.length > 0 && (
              <div className="mt-8 border-t border-gray-200 pt-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Project Videos</h2>
                  <div className="space-y-8">
                      {videos.map(video => (
                          <div key={video.id} className="bg-white p-4 rounded-lg shadow border border-gray-200">
                              <h3 className="text-lg font-medium text-gray-900">{video.title}</h3>
                              <div className="relative bg-gray-100 rounded h-64 overflow-hidden group mt-2 mb-4">
                                  {getVideoThumbnail(video.url) ? (
                                      <img src={getVideoThumbnail(video.url)} alt={video.title} className="w-full h-full object-cover" />
                                  ) : (
                                      <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400">Video Preview</div>
                                  )}
                                  <a href={video.url} target="_blank" rel="noopener noreferrer" className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-20 group-hover:bg-opacity-40 transition-all">
                                      <svg className="h-16 w-16 text-white opacity-90 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" /></svg>
                                  </a>
                              </div>
                              {token && <RateVideo videoId={video.id} />}
                              
                              {/* Comments Toggle */}
                              <div className="mt-4">
                                  <button 
                                    onClick={() => toggleComments(video.id)}
                                    className="text-sm text-indigo-600 hover:text-indigo-800 focus:outline-none"
                                  >
                                      {expandedVideoComments[video.id] ? 'Hide Comments' : 'Show Comments'}
                                  </button>
                              </div>

                              {/* Comments Section */}
                              {expandedVideoComments[video.id] && (
                                  <div className="mt-4 pl-4 border-l-2 border-gray-100">
                                      {videoComments[video.id] && videoComments[video.id].map(comment => (
                                          <div key={comment.id} className="mb-3">
                                              <p className="text-sm text-gray-800"><span className="font-semibold">{comment.user_name}:</span> {comment.content}</p>
                                              <p className="text-xs text-gray-400">{new Date(comment.created_at).toLocaleDateString()}</p>
                                          </div>
                                      ))}
                                      
                                      {token && (
                                          <div className="mt-4 flex">
                                              <input 
                                                type="text"
                                                className="flex-grow border border-gray-300 rounded-l-md px-3 py-2 text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                                placeholder="Ask a question..."
                                                value={newComment[video.id] || ''}
                                                onChange={(e) => setNewComment({ ...newComment, [video.id]: e.target.value })}
                                              />
                                              <button 
                                                onClick={() => handlePostComment(video.id)}
                                                className="bg-indigo-600 text-white px-4 py-2 rounded-r-md text-sm hover:bg-indigo-700"
                                              >
                                                  Post
                                              </button>
                                          </div>
                                      )}
                                  </div>
                              )}
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
                <span>{formatCurrency(project.current_funding)}</span>
                <span className="text-gray-500">goal {formatCurrency(project.funding_goal)}</span>
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

            {project.status === 'funding' ? (
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

      {/* More Like This */}
      {relatedProjects.length > 0 && (
          <div className="mt-12 border-t border-gray-200 pt-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">More Like This</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {relatedProjects.map(p => (
                      <ProjectCard key={p.id} project={p} />
                  ))}
              </div>
          </div>
      )}
    </div>
  );
};

export default ProjectDetail;
