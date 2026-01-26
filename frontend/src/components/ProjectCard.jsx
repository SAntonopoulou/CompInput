import React from 'react';
import { Link } from 'react-router-dom';
import { getVideoThumbnail } from '../utils/video';
import VerifiedBadge from './VerifiedBadge'; // Import the new component

const ProjectCard = ({ project }) => {
  const percentage = project.funding_goal > 0 ? (project.current_funding / project.funding_goal) * 100 : 0;
  const videoThumbnail = project.videos && project.videos.length > 0 ? getVideoThumbnail(project.videos[0].url) : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-full">
      <Link to={`/projects/${project.id}`}>
        <div className="h-48 bg-gray-200 flex items-center justify-center overflow-hidden">
          {videoThumbnail ? (
            <img src={videoThumbnail} alt={project.title} className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-500">Project Image</span>
          )}
        </div>
      </Link>
      <div className="p-6 flex flex-col flex-grow">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          <Link to={`/projects/${project.id}`} className="hover:text-indigo-600">{project.title}</Link>
        </h3>
        <p className="text-sm text-gray-600 mb-4 flex-grow">{project.description.substring(0, 100)}...</p>
        
        <div className="mb-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-bold text-indigo-600">
              €{(project.current_funding / 100).toFixed(2)}
            </span>
            <span className="text-sm text-gray-500">
              raised of €{(project.funding_goal / 100).toFixed(2)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-indigo-600 h-2.5 rounded-full" 
              style={{ width: `${percentage > 100 ? 100 : percentage}%` }}
            ></div>
          </div>
          <div className="text-right text-sm font-medium text-gray-700 mt-1">
            {Math.round(percentage)}% funded
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-gray-200">
          <div className="flex items-center">
            <Link to={`/profile/${project.teacher_id}`} className="w-10 h-10 bg-gray-300 rounded-full mr-3 overflow-hidden">
              {project.teacher_avatar_url ? (
                <img src={project.teacher_avatar_url} alt={project.teacher_name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gray-200"></div>
              )}
            </Link>
            <div className="flex-grow">
              <div className="flex items-center">
                <Link to={`/profile/${project.teacher_id}`} className="text-sm font-medium text-gray-900 hover:text-indigo-600">{project.teacher_name}</Link>
                <VerifiedBadge languages={project.teacher_verified_languages} />
              </div>
              <p className="text-sm text-gray-500">{project.language} - {project.level}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectCard;
