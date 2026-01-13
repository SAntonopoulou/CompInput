import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';

const CreateProject = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '', description: '', language: 'Japanese', level: 'N5', goal_amount: '', deadline: ''
  });

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Convert dollars to cents
      const payload = { ...formData, goal_amount: parseInt(formData.goal_amount) * 100 };
      await client.post('/projects/', payload);
      navigate('/teacher/dashboard');
    } catch (error) {
      console.error("Error creating project:", error);
      alert("Failed to create project");
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Create New Project</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Title</label>
          <input type="text" name="title" required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" onChange={handleChange} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea name="description" required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" rows="4" onChange={handleChange}></textarea>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Language</label>
            <select name="language" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" onChange={handleChange}>
              <option>Japanese</option><option>Spanish</option><option>French</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Level</label>
            <select name="level" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" onChange={handleChange}>
              <option>N5</option><option>N4</option><option>N3</option><option>A1</option><option>A2</option><option>B1</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Goal Amount ($)</label>
          <input type="number" name="goal_amount" required min="1" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" onChange={handleChange} />
        </div>
        <button type="submit" className="w-full bg-indigo-600 text-white py-2 px-4 rounded hover:bg-indigo-700">
          Create Project
        </button>
      </form>
    </div>
  );
};

export default CreateProject;