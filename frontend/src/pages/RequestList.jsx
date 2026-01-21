import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import ConfirmationModal from '../components/ConfirmationModal';
import { useToast } from '../context/ToastContext';

const RequestList = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [newRequest, setNewRequest] = useState({
    title: '',
    description: '',
    language: '',
    level: '',
    budget: 0,
    target_teacher_id: null,
    is_private: false
  });
  const [teacherSearch, setTeacherSearch] = useState('');
  const [teacherResults, setTeacherResults] = useState([]);
  const [selectedTeacherName, setSelectedTeacherName] = useState('');
  const [availableFilters, setAvailableFilters] = useState({ languages: [] });
  
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [requestToDelete, setRequestToDelete] = useState(null);

  const navigate = useNavigate();
  const { addToast } = useToast();
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      try {
        const [userRes, requestsRes, filtersRes] = await Promise.all([
          token ? client.get('/users/me') : Promise.resolve(null),
          client.get('/requests/'),
          client.get('/projects/filter-options')
        ]);
        
        if (userRes) setUser(userRes.data);
        setRequests(requestsRes.data);
        setAvailableFilters(filtersRes.data);

      } catch (error) {
        console.error('Error fetching data:', error);
        addToast('Error fetching data', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, [token, addToast]);

  useEffect(() => {
    const searchTeachers = async () => {
      if (teacherSearch.length > 0) {
        try {
          const response = await client.get('/users/teachers', { params: { query: teacherSearch } });
          setTeacherResults(response.data);
        } catch (error) { console.error("Failed to search teachers", error); }
      } else {
        setTeacherResults([]);
      }
    };
    const timeoutId = setTimeout(searchTeachers, 300);
    return () => clearTimeout(timeoutId);
  }, [teacherSearch]);

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...newRequest, budget: Math.round(newRequest.budget * 100) };
      await client.post('/requests/', payload);
      setShowModal(false);
      setNewRequest({ title: '', description: '', language: '', level: '', budget: 0, target_teacher_id: null, is_private: false });
      setSelectedTeacherName('');
      setTeacherSearch('');
      addToast('Request created successfully!', 'success');
      const response = await client.get('/requests/');
      setRequests(response.data);
    } catch (error) {
      console.error("Failed to create request", error);
      addToast('Failed to create request', 'error');
    }
  };

  const handleDiscussWithStudent = async (requestId) => {
    try {
      const response = await client.post('/conversations/', { request_id: requestId });
      addToast('Conversation started!', 'success');
      navigate(`/messages/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start conversation", error);
      addToast(error.response?.data?.detail || 'Failed to start conversation', 'error');
    }
  };

  const confirmDeleteRequest = (requestId) => {
      setRequestToDelete(requestId);
      setConfirmModalOpen(true);
  };

  const handleDeleteRequest = async () => {
      setConfirmModalOpen(false);
      if (!requestToDelete) return;
      try {
          await client.delete(`/requests/${requestToDelete}`);
          addToast('Request cancelled', 'success');
          const response = await client.get('/requests/');
          setRequests(response.data);
      } catch (error) {
          console.error("Failed to delete request", error);
          addToast(error.response?.data?.detail || "Failed to delete request", 'error');
      }
  };

  const formatCurrency = (amountInCents) => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amountInCents / 100);

  const allLanguages = availableFilters.languages.map(l => l.language);
  const allLevels = [...new Set(availableFilters.languages.flatMap(l => l.levels))];
  const userHasRequests = requests.some(req => req.user_id === user?.id);

  const renderEmptyState = () => (
    <div className="text-center py-16 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800">Don't see the content you need?</h2>
      <p className="mt-2 text-gray-600">Request it directly from our community of teachers.</p>
      <button onClick={() => setShowModal(true)} className="mt-6 inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none">
        Post Your First Request
      </button>
    </div>
  );

  const renderRequestHeader = () => (
    <div className="mb-8 p-6 bg-white rounded-lg shadow-md">
        <div className="flex justify-between items-center">
            <div>
                <h2 className="text-xl font-bold text-gray-800">Have another great idea?</h2>
                <p className="mt-1 text-gray-600">Let our teachers know what you'd like to see next.</p>
            </div>
            <button onClick={() => setShowModal(true)} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none">
                Post a Request
            </button>
        </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {loading ? <div className="text-center py-10">Loading...</div> : (
        <>
          {!userHasRequests && renderEmptyState()}
          {userHasRequests && renderRequestHeader()}
          
          <h1 className="text-3xl font-bold text-gray-900 mb-8 mt-8">Community Requests</h1>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {requests.map((req) => {
              if (user && user.role === 'teacher' && req.target_teacher_id && req.target_teacher_id !== user.id) return null;
              if (req.status !== 'open' && req.status !== 'negotiating' && (!user || user.id !== req.user_id)) return null;
              if (req.is_private && (!user || (user.id !== req.user_id && user.id !== req.target_teacher_id))) return null;

              return (
              <div key={req.id} className={`bg-white overflow-hidden shadow rounded-lg border ${req.target_teacher_id ? 'border-indigo-200 ring-1 ring-indigo-100' : 'border-gray-200'}`}>
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex justify-between items-start">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">{req.title}</h3>
                      <div className="flex flex-col items-end space-y-1">
                          {req.target_teacher_id && <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">Targeted</span>}
                          {req.is_private && <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">Private</span>}
                      </div>
                  </div>
                  <div className="flex space-x-2 mb-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{req.language}</span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{req.level}</span>
                  </div>
                  <p className="text-sm text-gray-500 mb-4 line-clamp-3">{req.description}</p>
                  <div className="mb-4">
                      <p className="text-sm font-medium text-gray-900">Budget: {formatCurrency(req.budget)}</p>
                  </div>
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                    <span className="text-xs text-gray-400">Requested by {req.user_name}</span>
                    {user && user.role === 'teacher' && req.status === 'open' && (
                      <div className="flex space-x-2">
                          <button onClick={() => handleDiscussWithStudent(req.id)} className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700">Discuss with Student</button>
                      </div>
                    )}
                    {user && user.id === req.user_id && (req.status === 'open' || req.status === 'negotiating') && <button onClick={() => confirmDeleteRequest(req.id)} className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded text-gray-500 bg-white hover:bg-gray-50">Cancel Request</button>}
                    {user && user.id === req.user_id && req.status === 'accepted' && <span className="text-xs text-green-500 font-medium">Accepted</span>}
                  </div>
                </div>
              </div>
            )})}
          </div>
        </>
      )}

      {showModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto"><div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true"><div className="absolute inset-0 bg-gray-500 opacity-75"></div></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleCreateRequest}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">What content do you want to see?</h3>
                  <p className="text-sm text-gray-500 mb-4">Describe the video you'd like a teacher to create. Be as specific as you can!</p>
                  <div className="space-y-4">
                    <div><label className="block text-sm font-medium text-gray-700">Title</label><input type="text" required className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={newRequest.title} onChange={(e) => setNewRequest({...newRequest, title: e.target.value})} /></div>
                    <div><label className="block text-sm font-medium text-gray-700">Description</label><textarea required rows={3} className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={newRequest.description} onChange={(e) => setNewRequest({...newRequest, description: e.target.value})} /></div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Language</label>
                        <input type="text" list="languages" required className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={newRequest.language} onChange={(e) => setNewRequest({...newRequest, language: e.target.value})} />
                        <datalist id="languages">{allLanguages.map(lang => <option key={lang} value={lang} />)}</datalist>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Level</label>
                        <input type="text" list="levels" required className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={newRequest.level} onChange={(e) => setNewRequest({...newRequest, level: e.target.value})} />
                        <datalist id="levels">{allLevels.map(lvl => <option key={lvl} value={lvl} />)}</datalist>
                      </div>
                    </div>
                    <div><label className="block text-sm font-medium text-gray-700">Budget (EUR)</label><input type="number" min="0" className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={newRequest.budget} onChange={(e) => setNewRequest({...newRequest, budget: e.target.value})} /></div>
                    <div className="relative">
                        <label className="block text-sm font-medium text-gray-700">Target Teacher (Optional)</label>
                        <input type="text" placeholder="Search by name..." className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={selectedTeacherName || teacherSearch} onChange={(e) => { setTeacherSearch(e.target.value); setSelectedTeacherName(''); setNewRequest({...newRequest, target_teacher_id: null}); }} />
                        {teacherResults.length > 0 && !selectedTeacherName && (
                            <ul className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                                {teacherResults.map((teacher) => <li key={teacher.id} className="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-indigo-600 hover:text-white" onClick={() => { setNewRequest({...newRequest, target_teacher_id: teacher.id}); setSelectedTeacherName(teacher.full_name); setTeacherResults([]); }}>{teacher.full_name}</li>)}
                            </ul>
                        )}
                    </div>
                    {newRequest.target_teacher_id && <div className="flex items-center"><input id="is_private" name="is_private" type="checkbox" className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" checked={newRequest.is_private} onChange={(e) => setNewRequest({...newRequest, is_private: e.target.checked})} /><label htmlFor="is_private" className="ml-2 block text-sm text-gray-900">Private Request (Only visible to target teacher)</label></div>}
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button type="submit" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">Post Request</button>
                  <button type="button" onClick={() => setShowModal(false)} className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">Cancel</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      <ConfirmationModal isOpen={confirmModalOpen} onClose={() => setConfirmModalOpen(false)} onConfirm={handleDeleteRequest} title="Cancel Request" message="Are you sure you want to cancel this request? This cannot be undone." confirmText="Cancel Request" isDanger={true} />
    </div>
  );
};

export default RequestList;
