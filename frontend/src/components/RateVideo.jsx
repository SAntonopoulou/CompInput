import React, { useState } from 'react';
import client from '../api/client';

const RateVideo = ({ videoId, initialRating = 0 }) => {
  const [rating, setRating] = useState(initialRating);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    try {
      await client.post(`/videos/${videoId}/rate`, { rating, comment });
      setSubmitted(true);
    } catch (error) {
      console.error("Failed to submit rating", error);
      alert("Failed to submit rating");
    }
  };

  if (submitted) {
      return <div className="text-sm text-green-600 font-medium">Thanks for rating!</div>;
  }

  return (
    <div className="mt-2">
      <div className="flex items-center">
        {[...Array(5)].map((star, index) => {
          const ratingValue = index + 1;
          return (
            <button
              type="button"
              key={index}
              className={`text-xl focus:outline-none ${
                ratingValue <= (hover || rating) ? "text-yellow-400" : "text-gray-300"
              }`}
              onClick={() => setRating(ratingValue)}
              onMouseEnter={() => setHover(ratingValue)}
              onMouseLeave={() => setHover(rating)}
            >
              ★
            </button>
          );
        })}
        <span className="ml-2 text-xs text-gray-500">{rating > 0 ? `${rating}/5` : 'Rate this video'}</span>
      </div>
      {rating > 0 && (
          <div className="mt-2 flex items-center space-x-2">
              <input 
                type="text" 
                placeholder="Optional comment..." 
                className="text-xs border border-gray-300 rounded px-2 py-1 w-full"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              <button 
                onClick={handleSubmit}
                className="text-xs bg-indigo-600 text-white px-2 py-1 rounded hover:bg-indigo-700"
              >
                  Submit
              </button>
          </div>
      )}
    </div>
  );
};

export default RateVideo;
