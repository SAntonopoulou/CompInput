import React, { useState, useEffect } from 'react';
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

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await client.get('/users/me');
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user", error);
        addToast("Could not load user data.", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [addToast]);

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

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      {user && user.role === 'teacher' && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Payouts Setup
            </h3>
            <div className="mt-2 max-w-xl text-sm text-gray-500">
              {user.charges_enabled ? (
                <p>Your payout account is active and ready to receive funds.</p>
              ) : (
                <p>Connect with Stripe to receive payments for your funded projects.</p>
              )}
            </div>
            <div className="mt-5">
              <button
                type="button"
                onClick={handleStripeOnboarding}
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
              >
                {user.charges_enabled ? 'Manage Payout Account' : 'Set up Payouts'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Danger Zone
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>
              Once you delete your account, there is no going back. Please be certain.
            </p>
          </div>
          <div className="mt-5">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:text-sm"
            >
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
