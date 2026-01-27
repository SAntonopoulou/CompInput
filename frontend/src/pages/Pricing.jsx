import React from 'react';
import client from '../api/client'; // Import the configured axios client
import { useAuth } from '../context/AuthContext'; 

const tiers = [
  {
    name: 'Student Plus',
    id: 'plus',
    price: '$5',
    description: 'Get a head start on your learning journey.',
    features: [
      'Access to exclusive content',
      'Priority support',
      'Early access to new features',
    ],
  },
  {
    name: 'Student Premium',
    id: 'premium',
    price: '$15',
    description: 'Supercharge your learning with premium benefits.',
    features: [
      'All features of Student Plus',
      'One monthly Priority Credit for requests',
      'Premium badge on your profile',
    ],
  },
  {
    name: 'Teacher Pro',
    id: 'pro',
    price: '$25',
    description: 'Unlock professional tools to grow your audience.',
    features: [
      'Submit language verifications',
      'Pro badge on your profile',
      'Advanced analytics on your projects',
    ],
  },
];

const PricingPage = () => {
  const { token } = useAuth();

  const handleChoosePlan = async (planId) => {
    try { 
      const response = await client.post(
        '/subscriptions/create-checkout-session',
        { plan_id: planId },
      );
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      // You might want to show an error message to the user
    }
  };

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold text-center mb-4">Choose Your Plan</h1>
      <p className="text-lg text-gray-600 text-center mb-12">
        Unlock new features and support the platform.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {tiers.map((tier) => (
          <div
            key={tier.id}
            className="bg-white rounded-lg shadow-lg p-8 flex flex-col"
          >
            <h2 className="text-2xl font-bold mb-2">{tier.name}</h2>
            <p className="text-4xl font-extrabold mb-4">
              {tier.price}
              <span className="text-lg font-medium text-gray-500">/month</span>
            </p>
            <p className="text-gray-600 mb-6">{tier.description}</p>
            <ul className="space-y-4 text-gray-700 mb-8 flex-grow">
              {tier.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <svg
                    className="w-6 h-6 text-green-500 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M5 13l4 4L19 7"
                    ></path>
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleChoosePlan(tier.id)}
              className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Choose Plan
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PricingPage;
