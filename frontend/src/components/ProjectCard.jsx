import React from 'react';
import { Link } from 'react-router-dom';

const ProjectCard = ({ project }) => {
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

  const tags = project.tags ? project.tags.split(',').map(t => t.trim()) : [];

  const getInitials = (name) => {
      return name ? name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '??';
  };

  return (
    <div className="block bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden border border-gray-200 flex flex-col h-full">
      <div className="p-6 flex-grow">
        <div className="flex justify-between items-start mb-4">
          <Link to={`/projects/${project.id}`} className="hover:underline">
            <h3 className="text-xl font-bold text-gray-900 line-clamp-2">
                {project.title}
            </h3>
          </Link>
        </div>
        
        <div className="flex items-center mb-4">
          {project.requester_name ? (
              <>
                {project.requester_avatar_url ? (
                    <img src={project.requester_avatar_url} alt={project.requester_name} className="h-6 w-6 rounded-full object-cover mr-2" />
                ) : (
                    <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs mr-2">
                        {getInitials(project.requester_name)}
                    </div>
                )}
                <span className="text-sm text-gray-600">
                    Requested by <Link to={`/profile/${project.requester_id}`} className="font-medium text-indigo-600 hover:underline">{project.requester_name}</Link>
                </span>
              </>
          ) : (
              <>
                {project.teacher_avatar_url ? (
                    <img src={project.teacher_avatar_url} alt={project.teacher_name} className="h-6 w-6 rounded-full object-cover mr-2" />
                ) : (
                    <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs mr-2">
                        {getInitials(project.teacher_name)}
                    </div>
                )}
                <span className="text-sm text-gray-600">
                    by <Link to={`/profile/${project.teacher_id}`} className="font-medium text-indigo-600 hover:underline">{project.teacher_name}</Link>
                </span>
              </>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {project.language}
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {project.level}
          </span>
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-sm font-medium text-gray-900 mb-1">
            <span>{formatCurrency(project.current_amount)}</span>
            <span className="text-gray-500">of {formatCurrency(project.goal_amount)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-indigo-600 h-2.5 rounded-full"
              style={{ width: `${percentage}%` }}
            ></div>
          </div>
        </div>
      </div>
      
      {tags.length > 0 && (
          <div className="px-6 pb-4">
              <div className="flex flex-wrap gap-1">
                  {tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {tag}
                      </span>
                  ))}
                  {tags.length > 3 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          +{tags.length - 3}
                      </span>
                  )}
              </div>
          </div>
      )}
    </div>
  );
};

export default ProjectCard;
