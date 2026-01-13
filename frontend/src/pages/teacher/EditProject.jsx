import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../../api/client';

const EditProject = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    language: '',
    level: '',
    goal_amount: 0,
    delivery_days: 0,
    status: ''
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await client.get(`/projects/${id}`);
        setProject(response.data);
        setFormData({
          title: response.data.title,
          description: response.data.description,
          language: response.data.language,
          level: response.data.level,
          goal_amount: response.data.goal_amount / 100, // Convert cents to dollars for form
          delivery_days: response.data.delivery_days || 7,
          status: response.data.status
        });
      } catch (err) {
        console.error(err);
        setError("Failed to load project.");
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [id]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = {
        ...formData,
        goal_amount: Math.round(formData.goal_amount * 100), // Convert dollars to cents
      };
      if (payload.delivery_days) {
          payload.delivery_days = parseInt(payload.delivery_days);
      }
      await client.patch(`/projects/${id}`, payload);
      navigate('/teacher/dashboard');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to update project.");
    }
  };

  if (loading) return <div className="p-10 text-center">Loading project...</div>;
  if (error && !project) return <div className="p-10 text-center text-red-600">{error}</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Edit Project</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-8 space-y-6">
        {error && <div className="text-red-600">{error}</div>}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Title</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Goal Amount (USD)</label>
            <input
              type="number"
              name="goal_amount"
              value={formData.goal_amount}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
              required
              min="1"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            name="description"
            rows={5}
            value={formData.description}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Language</label>
            <select
              name="language"
              value={formData.language}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
            >
              <option>Japanese</option>
              <option>Spanish</option>
              <option>French</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Level</label>
            <select
              name="level"
              value={formData.level}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
            >
              <option>N5</option>
              <option>N4</option>
              <option>N3</option>
              <option>N2</option>
              <option>N1</option>
              <option>A1</option>
              <option>A2</option>
              <option>B1</option>
              <option>B2</option>
              <option>C1</option>
              <option>C2</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Days to Deliver</label>
          <input
            type="number"
            name="delivery_days"
            value={formData.delivery_days}
            onChange={handleChange}
            min="1"
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
          />
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Save Changes
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditProject;
