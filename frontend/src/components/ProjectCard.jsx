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

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden border border-gray-200"
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-bold text-gray-900 line-clamp-2">
            {project.title}
          </h3>
        </div>
        
        <p className="text-sm text-gray-600 mb-4">
          by <span className="font-medium text-indigo-600">{project.teacher_name}</span>
        </p>

        <div className="flex space-x-2 mb-4">
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
    </Link>
  );
};

export default ProjectCard;
