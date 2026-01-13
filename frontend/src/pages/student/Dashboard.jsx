import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';

const StudentDashboard = () => {
  const [pledges, setPledges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPledges = async () => {
      try {
        const response = await client.get('/pledges/me');
        setPledges(response.data);
      } catch (error) {
        console.error("Failed to fetch pledges", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPledges();
  }, []);

  const formatCurrency = (amountInCents) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amountInCents / 100);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) return <div className="p-10 text-center">Loading dashboard...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Pledges</h1>
      
      {pledges.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-6 text-center">
          <p className="text-gray-500 mb-4">You haven't backed any projects yet.</p>
          <Link to="/" className="text-indigo-600 hover:text-indigo-800 font-medium">
            Browse Projects
          </Link>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Project
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {pledges.map((pledge) => (
                <tr key={pledge.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link to={`/projects/${pledge.project_id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                      {pledge.project_title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(pledge.amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(pledge.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        pledge.status === 'captured' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                        Pledge: {pledge.status}
                        </span>
                        <span className="text-xs text-gray-400 mt-1">
                            Project: {pledge.project_status}
                        </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;
