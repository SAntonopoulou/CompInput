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
  const [editForm, setEditForm] = useState({ bio: '', languages: '', intro_video_url: '', sample_video_url: '', avatar_url: '' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileRes = await client.get(`/users/${id}/profile`);
        setProfile(profileRes.data);
        setEditForm({ 
            bio: profileRes.data.bio || '', 
            languages: profileRes.data.languages || '',
            intro_video_url: profileRes.data.intro_video_url || '',
            sample_video_url: profileRes.data.sample_video_url || '',
            avatar_url: profileRes.data.avatar_url || ''
        });

        const token = localStorage.getItem('token');
        if (token) {
            try {
                const userRes = await client.get('/users/me');
                setCurrentUser(userRes.data);
            } catch (e) {
                console.error("Failed to fetch current user");
            }
        }

        if (profileRes.data.role === 'teacher') {
            const videosRes = await client.get('/videos/', { params: { teacher_id: id } });
            setHistory(videosRes.data);
        } else {
            setHistory([]);
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
  const getInitials = (name) => name ? name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '??';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <div className="flex items-center">
            {profile.avatar_url ? (
                <img 
                    src={profile.avatar_url} 
                    alt={profile.full_name} 
                    className="h-16 w-16 rounded-full object-cover mr-4"
                    onError={(e) => { e.target.onerror = null; e.target.src = `https://ui-avatars.com/api/?name=${profile.full_name}&background=random`; }}
                />
            ) : (
                <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xl mr-4">
                    {getInitials(profile.full_name)}
                </div>
            )}
            <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">{profile.full_name}</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    {profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
                    {profile.role === 'teacher' && profile.average_rating != null && (
                        <span className="ml-3 inline-flex items-center">
                            <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                            <span className="ml-1 font-bold text-gray-700">{profile.average_rating}</span>
                            <Link to={`/teacher/${profile.id}/reviews`} className="ml-3 text-xs text-indigo-600 hover:underline">See all reviews</Link>
                        </span>
                    )}
                </p>
            </div>
          </div>
          {isOwner && <button onClick={() => setIsEditing(!isEditing)} className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">{isEditing ? 'Cancel' : 'Edit Profile'}</button>}
        </div>

        {!isEditing && profile.intro_video_url && (
            <div className="px-4 py-5 sm:px-6 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Introduction</h4>
                <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded flex items-center justify-center h-64">
                    <a href={profile.intro_video_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center"><svg className="h-12 w-12 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" /></svg>Watch Intro Video</a>
                </div>
            </div>
        )}

        <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
          <dl className="sm:divide-y sm:divide-gray-200">
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Bio</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{isEditing ? <textarea className="w-full border border-gray-300 rounded-md p-2" rows={3} value={editForm.bio} onChange={(e) => setEditForm({...editForm, bio: e.target.value})} /> : (profile.bio || "No bio provided.")}</dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Languages</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{isEditing ? <input type="text" className="w-full border border-gray-300 rounded-md p-2" value={editForm.languages} onChange={(e) => setEditForm({...editForm, languages: e.target.value})} placeholder="e.g. Japanese, Spanish" /> : (profile.languages || "None listed.")}</dd>
            </div>
            {isEditing && (
                <>
                    <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Avatar URL</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2"><input type="url" className="w-full border border-gray-300 rounded-md p-2" value={editForm.avatar_url} onChange={(e) => setEditForm({...editForm, avatar_url: e.target.value})} placeholder="https://example.com/my-avatar.jpg" /></dd>
                    </div>
                    <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Intro Video URL</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2"><input type="url" className="w-full border border-gray-300 rounded-md p-2" value={editForm.intro_video_url} onChange={(e) => setEditForm({...editForm, intro_video_url: e.target.value})} placeholder="https://youtube.com/..." /></dd>
                    </div>
                    <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">Sample Video URL</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2"><input type="url" className="w-full border border-gray-300 rounded-md p-2" value={editForm.sample_video_url} onChange={(e) => setEditForm({...editForm, sample_video_url: e.target.value})} placeholder="https://youtube.com/..." /></dd>
                    </div>
                </>
            )}
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Joined</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{new Date(profile.created_at).toLocaleDateString()}</dd>
            </div>
          </dl>
        </div>
        {isEditing && <div className="px-4 py-3 bg-gray-50 text-right sm:px-6"><button onClick={handleUpdate} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none">Save</button></div>}
      </div>

      {!isEditing && profile.sample_video_url && (
          <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Teaching Sample</h3>
              <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded flex items-center justify-center h-64"><a href={profile.sample_video_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center"><svg className="h-12 w-12 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" /></svg>Watch Sample Lesson</a></div>
          </div>
      )}

      {profile.role === 'teacher' && (
          <div className="mt-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Videos</h3>
              {history.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {history.map(video => (
                          <div key={video.id} className="bg-white p-4 rounded-lg shadow border border-gray-200">
                              <h4 className="font-bold text-gray-900">{video.title}</h4>
                              <p className="text-sm text-gray-500">{video.project_title}</p>
                              <a href={video.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 text-sm hover:underline mt-2 block">Watch Video</a>
                          </div>
                      ))}
                  </div>
              ) : (<p className="text-gray-500">No videos found.</p>)}
          </div>
      )}
    </div>
  );
};

export default Profile;
