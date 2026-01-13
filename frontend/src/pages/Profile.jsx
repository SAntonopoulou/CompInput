import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';

const Profile = () => {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ bio: '', languages: '' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Profile
        const profileRes = await client.get(`/users/${id}/profile`);
        setProfile(profileRes.data);
        setEditForm({ 
            bio: profileRes.data.bio || '', 
            languages: profileRes.data.languages || '' 
        });

        // Fetch Current User
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const userRes = await client.get('/users/me');
                setCurrentUser(userRes.data);
            } catch (e) {
                console.error("Failed to fetch current user");
            }
        }

        // Fetch History based on Role
        if (profileRes.data.role === 'teacher') {
            const videosRes = await client.get('/videos/', { params: { teacher_id: id } });
            setHistory(videosRes.data);
        } else {
            const pledgesRes = await client.get(`/pledges/user/${id}`);
            setHistory(pledgesRes.data);
        }

      } catch (error) {
        console.error("Failed to fetch profile", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleUpdate = async () => {
      try {
          await client.patch('/users/me', editForm);
          setProfile({ ...profile, ...editForm });
          setIsEditing(false);
      } catch (error) {
          console.error("Failed to update profile", error);
          alert("Failed to update profile");
      }
  };

  if (loading) return <div className="p-10 text-center">Loading profile...</div>;
  if (!profile) return <div className="p-10 text-center">User not found</div>;

  const isOwner = currentUser && currentUser.id === profile.id;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              {profile.full_name}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              {profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
            </p>
            {profile.role === 'teacher' && profile.average_rating && (
                <div className="mt-2 flex items-center">
                    <span className="text-yellow-400 text-lg mr-1">★</span>
                    <span className="text-sm font-bold text-gray-900">{profile.average_rating} / 5</span>
                </div>
            )}
          </div>
          {isOwner && (
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
              >
                  {isEditing ? 'Cancel' : 'Edit Profile'}
              </button>
          )}
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
          <dl className="sm:divide-y sm:divide-gray-200">
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Bio</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {isEditing ? (
                    <textarea
                        className="w-full border border-gray-300 rounded-md p-2"
                        rows={3}
                        value={editForm.bio}
                        onChange={(e) => setEditForm({...editForm, bio: e.target.value})}
                    />
                ) : (
                    profile.bio || "No bio provided."
                )}
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Languages</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {isEditing ? (
                    <input
                        type="text"
                        className="w-full border border-gray-300 rounded-md p-2"
                        value={editForm.languages}
                        onChange={(e) => setEditForm({...editForm, languages: e.target.value})}
                        placeholder="e.g. Japanese, Spanish"
                    />
                ) : (
                    profile.languages || "None listed."
                )}
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Joined</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {new Date(profile.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>
        {isEditing && (
            <div className="px-4 py-3 bg-gray-50 text-right sm:px-6">
                <button
                    onClick={handleUpdate}
                    className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
                >
                    Save
                </button>
            </div>
        )}
      </div>

      {/* History Section */}
      <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
              {profile.role === 'teacher' ? 'Recent Videos' : 'Backed Projects'}
          </h3>
          {history.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {history.map(item => (
                      <div key={item.id || item.project_id} className="bg-white p-4 rounded-lg shadow border border-gray-200">
                          {profile.role === 'teacher' ? (
                              <>
                                  <h4 className="font-bold text-gray-900">{item.title}</h4>
                                  <p className="text-sm text-gray-500">{item.project_title}</p>
                                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 text-sm hover:underline mt-2 block">
                                      Watch Video
                                  </a>
                              </>
                          ) : (
                              <>
                                  <h4 className="font-bold text-gray-900">
                                      <Link to={`/projects/${item.project_id}`} className="hover:underline">
                                          {item.project_title}
                                      </Link>
                                  </h4>
                                  <p className="text-xs text-gray-500">
                                      Backed on {new Date(item.created_at).toLocaleDateString()}
                                  </p>
                              </>
                          )}
                          </div>
                      ))}
                  </div>
              ) : (
                  <p className="text-gray-500">No videos found.</p>
              )}
          </div>
    </div>
  );
};

export default Profile;
