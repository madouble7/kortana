import React, { useState, useEffect } from 'react';
import { auth, signInWithGoogle, logout } from '../firebase';
import { onAuthStateChanged, User } from 'firebase/auth';
import { LogIn, LogOut, User as UserIcon, Loader2 } from 'lucide-react';

export default function UserMenu() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) {
    return <Loader2 className="animate-spin text-gray-400" size={20} />;
  }

  if (!user) {
    return (
      <button
        onClick={signInWithGoogle}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm font-medium"
      >
        <LogIn size={16} />
        <span>Sign In</span>
      </button>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        {user.photoURL ? (
          <img
            src={user.photoURL}
            alt={user.displayName || 'User'}
            className="w-8 h-8 rounded-full border border-gray-200 dark:border-gray-700"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-500">
            <UserIcon size={16} />
          </div>
        )}
        <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300">
          {user.displayName?.split(' ')[0]}
        </span>
      </div>
      <button
        onClick={logout}
        className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
        title="Logout"
      >
        <LogOut size={18} />
      </button>
    </div>
  );
}
