import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import client from '../api/client';
import { stripePromise } from '../utils/stripe';

const CheckoutForm = ({ onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [message, setMessage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);

    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        // Return URL where the customer should be redirected after the payment
        return_url: window.location.href,
      },
      redirect: "if_required",
    });

    if (error) {
      setMessage(error.message);
    } else if (paymentIntent && paymentIntent.status === "succeeded") {
      setMessage("Payment succeeded!");
      if (onSuccess) onSuccess();
    } else {
      setMessage("Unexpected state");
    }

    setIsProcessing(false);
  };

  return (
    <form onSubmit={handleSubmit} className="mt-4">
      <PaymentElement />
      <button
        disabled={isProcessing || !stripe || !elements}
        id="submit"
        className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
      >
        <span id="button-text">
          {isProcessing ? "Processing..." : "Pay Now"}
        </span>
      </button>
      {message && <div id="payment-message" className="mt-2 text-sm text-red-600">{message}</div>}
    </form>
  );
};

const PledgeForm = ({ projectId, projectName }) => {
  const [amount, setAmount] = useState(10); // Default $10
  const [clientSecret, setClientSecret] = useState(null);
  const [step, setStep] = useState('amount');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleAmountSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const amountInCents = Math.round(amount * 100);
      if (amountInCents < 50) { // Stripe minimum is usually 50 cents
          setError("Minimum pledge is $0.50");
          return;
      }

      const response = await client.post('/pledges/', {
        project_id: projectId,
        amount: amountInCents,
      });

      setClientSecret(response.data.client_secret);
      setStep('payment');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to initialize pledge");
    }
  };

  if (success) {
      return (
          <div className="bg-green-50 p-6 rounded-lg border border-green-200 text-center">
              <h3 className="text-lg font-medium text-green-800">Thank you for your pledge!</h3>
              <p className="mt-2 text-green-600">You have successfully backed {projectName}.</p>
          </div>
      )
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Back this Project</h3>
      
      {step === 'amount' ? (
        <form onSubmit={handleAmountSubmit}>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">
            Pledge Amount (USD)
          </label>
          <div className="relative rounded-md shadow-sm mb-4">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <input
              type="number"
              name="amount"
              id="amount"
              className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md py-2 border"
              placeholder="0.00"
              min="1"
              step="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          
          {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

          <button
            type="submit"
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors"
          >
            Continue to Payment
          </button>
        </form>
      ) : (
        <div>
            <div className="mb-4 flex justify-between items-center">
                <span className="text-sm text-gray-500">Pledging ${amount}</span>
                <button 
                    onClick={() => setStep('amount')}
                    className="text-xs text-indigo-600 hover:text-indigo-800"
                >
                    Change Amount
                </button>
            </div>
            {clientSecret && (
                <Elements stripe={stripePromise} options={{ clientSecret }}>
                <CheckoutForm onSuccess={() => setSuccess(true)} />
                </Elements>
            )}
        </div>
      )}
    </div>
  );
};

export default PledgeForm;
