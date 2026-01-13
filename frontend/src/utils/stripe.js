import { loadStripe } from '@stripe/stripe-js';

// Replace with your actual publishable key
const STRIPE_PUBLIC_KEY = import.meta.env.VITE_STRIPE_PUBLIC_KEY;

export const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);
