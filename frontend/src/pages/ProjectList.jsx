import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import client from '../api/client';
import ProjectCard from '../components/ProjectCard';

const ITEMS_PER_PAGE = 9;

const ProjectList = () => {
  const [projects, setProjects] = useState([]);
  const [filters, setFilters] = useState({
    language: '',
    level: '',
    tag: '',
    search: ''
  });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  
  const location = useLocation();
  const navigate = useNavigate();

  // Parse query params on load
  useEffect(() => {
      const searchParams = new URLSearchParams(location.search);
      const search = searchParams.get('search') || '';
      if (search) {
          setFilters(prev => ({ ...prev, search }));
      }
  }, [location.search]);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const offset = (page - 1) * ITEMS_PER_PAGE;
        const params = {
            limit: ITEMS_PER_PAGE,
            offset: offset
        };
        if (filters.language) params.language = filters.language;
        if (filters.level) params.level = filters.level;
        if (filters.tag) params.tag = filters.tag;
        if (filters.search) params.search = filters.search;

        const response = await client.get('/projects/', { params });
        setProjects(response.data);
      } catch (error) {
        console.error('Error fetching projects:', error);
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(fetchProjects, 300);
    return () => clearTimeout(timeoutId);
  }, [filters, page]);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
    setPage(1); // Reset to page 1 on filter change
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Discover Projects
          </h1>
          <input
            type="text"
            name="search"
            value={filters.search}
            onChange={handleFilterChange}
            placeholder="Search projects by title or description..."
            className="block w-full px-4 py-3 text-lg border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
      </div>
      
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 space-y-4 md:space-y-0 md:space-x-4">
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 w-full">
          <select
            name="language"
            value={filters.language}
            onChange={handleFilterChange}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">All Languages</option>
            <option value="Japanese">Japanese</option>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
            <option value="German">German</option>
            <option value="Chinese">Chinese</option>
          </select>

          <select
            name="level"
            value={filters.level}
            onChange={handleFilterChange}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">All Levels</option>
            <option value="N5">N5 (Beginner)</option>
            <option value="N4">N4</option>
            <option value="N3">N3</option>
            <option value="N2">N2</option>
            <option value="N1">N1 (Advanced)</option>
            <option value="A1">A1 (Beginner)</option>
            <option value="A2">A2</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
            <option value="C2">C2 (Advanced)</option>
          </select>

          <input
            type="text"
            name="tag"
            value={filters.tag}
            onChange={handleFilterChange}
            placeholder="Filter by Tag"
            className="block w-full pl-3 pr-3 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading projects...</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-10 bg-white rounded-lg shadow">
          <p className="text-gray-500 text-lg mb-4">No projects found matching your criteria.</p>
          <Link
            to="/requests"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
          >
            Request a video instead!
          </Link>
        </div>
      ) : (
        <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
            ))}
            </div>
            
            {/* Pagination Controls */}
            <div className="flex justify-center space-x-4">
                <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Previous
                </button>
                <span className="px-4 py-2 text-sm text-gray-700 flex items-center">
                    Page {page}
                </span>
                <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={projects.length < ITEMS_PER_PAGE}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Next
                </button>
            </div>
        </>
      )}
    </div>
  );
};

export default ProjectList;
