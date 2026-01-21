import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import ConfirmationModal from '../components/ConfirmationModal';
import { useToast } from '../context/ToastContext';

const Settings = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifications, setVerifications] = useState([]);
  const [newVerification, setNewVerification] = useState({ language: '', document_url: '' });

  const fetchUserData = useCallback(async () => {
    try {
      const userRes = await client.get('/users/me');
      setUser(userRes.data);
      if (userRes.data.role === 'teacher') {
        const verificationsRes = await client.get('/verifications/me');
        setVerifications(verificationsRes.data);
      }
    } catch (error) {
      console.error("Failed to fetch user data", error);
      addToast("Could not load user data.", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const handleDeleteAccount = async () => {
    setModalOpen(false);
    try {
      await client.delete('/users/me');
      localStorage.removeItem('token');
      navigate('/');
      window.location.reload();
    } catch (error) {
      console.error("Failed to delete account", error);
      addToast("Failed to delete account. Please try again.", 'error');
    }
  };

  const handleStripeOnboarding = async () => {
    try {
      const response = await client.post('/users/stripe-onboarding-link');
      window.location.href = response.data.onboarding_url;
    } catch (error) {
      console.error("Stripe onboarding failed", error);
      addToast("Could not start Stripe onboarding. Please try again.", "error");
    }
  };

  const handleVerificationSubmit = async (e) => {
    e.preventDefault();
    if (!newVerification.language || !newVerification.document_url) {
      addToast("Please fill out both fields.", "error");
      return;
    }
    try {
      await client.post('/verifications/', newVerification);
      addToast("Verification request submitted!", "success");
      setNewVerification({ language: '', document_url: '' });
      fetchUserData(); // Refresh verifications list
    } catch (error) {
      addToast(error.response?.data?.detail || "Failed to submit request.", "error");
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      {user && user.role === 'teacher' && (
        <>
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Language Verifications</h3>
              <p className="mt-2 max-w-xl text-sm text-gray-500">Submit documents to get a "Verified" badge for languages you're certified in.</p>
              
              <form onSubmit={handleVerificationSubmit} className="mt-5 sm:flex sm:items-center">
                <div className="w-full sm:max-w-xs">
                  <input type="text" value={newVerification.language} onChange={(e) => setNewVerification({...newVerification, language: e.target.value})} placeholder="Language (e.g., Japanese)" className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"/>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-3 w-full">
                  <input type="url" value={newVerification.document_url} onChange={(e) => setNewVerification({...newVerification, document_url: e.target.value})} placeholder="Link to Certificate (e.g., Google Drive)" className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"/>
                </div>
                <button type="submit" className="mt-3 sm:mt-0 sm:ml-3 w-full sm:w-auto inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm">Submit</button>
              </form>

              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-800">Your Submissions</h4>
                {verifications.length === 0 ? <p className="text-sm text-gray-500 mt-2">No submissions yet.</p> : (
                  <ul className="mt-2 border border-gray-200 rounded-md divide-y divide-gray-200">
                    {verifications.map(v => (
                      <li key={v.id} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                        <div className="w-0 flex-1 flex items-center">
                          <span className="ml-2 flex-1 w-0 truncate">{v.language}</span>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            v.status === 'approved' ? 'bg-green-100 text-green-800' : 
                            v.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {v.status}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Payouts</h3>
              <div className="mt-2 max-w-xl text-sm text-gray-500">
                {user.charges_enabled ? <p>Your payout account is active. You can manage your account details on Stripe.</p> : <p>Connect with Stripe to receive payments for your funded projects.</p>}
              </div>
              <div className="mt-5">
                <button type="button" onClick={handleStripeOnboarding} className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm">
                  {user.charges_enabled ? 'Edit Your Payouts' : 'Set up Payouts'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Danger Zone</h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500"><p>Once you delete your account, there is no going back. Please be certain.</p></div>
          <div className="mt-5">
            <button type="button" onClick={() => setModalOpen(true)} className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:text-sm">
              Delete Account
            </button>
          </div>
        </div>
      </div>

      <ConfirmationModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleDeleteAccount}
        title="Delete Account"
        message="Are you sure? This cannot be undone. Your projects and pledges will be anonymized."
        confirmText="Delete Account"
        isDanger={true}
      />
    </div>
  );
};

export default Settings;
