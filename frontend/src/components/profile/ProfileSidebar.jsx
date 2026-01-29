const ProfileSidebar = ({ user, activeTab, setActiveTab, onLogout }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="text-center">
        <div className="mb-4">
          <i className="fas fa-user-circle text-5xl text-yellow-400"></i>
        </div>
        <h4 className="text-lg font-semibold text-white">{user?.full_name || user?.username}</h4>
        <p className="text-sm text-gray-400">@{user?.username}</p>

        <div className="bg-gray-700 rounded-lg p-3 mt-4">
          <h5 className="text-sm font-medium text-yellow-400">About Arbify</h5>
          <p className="text-xs text-gray-300 mt-1">Arbify helps you find betting opportunities across sportsbooks.</p>
          <p className="text-xs text-gray-300 mt-1">We don't handle any funds - we just show you where to place your bets.</p>
        </div>
      </div>

      <div className="mt-6">
        <h5 className="text-sm font-medium text-yellow-400 mb-3">Quick Links</h5>
        <nav className="space-y-1">
          <button
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center p-2 rounded-md text-sm ${activeTab === 'profile'
                ? 'bg-yellow-400 text-gray-900'
                : 'text-gray-300 hover:bg-gray-700'
              }`}
          >
            <i className="fas fa-user mr-3"></i>
            Profile
          </button>

          <button
            onClick={() => setActiveTab('security')}
            className={`w-full flex items-center p-2 rounded-md text-sm ${activeTab === 'security'
                ? 'bg-yellow-400 text-gray-900'
                : 'text-gray-300 hover:bg-gray-700'
              }`}
          >
            <i className="fas fa-shield-alt mr-3"></i>
            Security
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`w-full flex items-center p-2 rounded-md text-sm ${activeTab === 'preferences'
                ? 'bg-yellow-400 text-gray-900'
                : 'text-gray-300 hover:bg-gray-700'
              }`}
          >
            <i className="fas fa-cog mr-3"></i>
            Preferences
          </button>

          <button
            onClick={() => setActiveTab('myArbitrage')}
            className={`w-full flex items-center p-2 rounded-md text-sm ${activeTab === 'myArbitrage'
                ? 'bg-yellow-400 text-gray-900'
                : 'text-gray-300 hover:bg-gray-700'
              }`}
          >
            <i className="fas fa-percentage mr-3"></i>
            My Arbitrage
          </button>
        </nav>

        <button
          onClick={onLogout}
          className="w-full mt-6 btn-outline-danger flex items-center justify-center"
        >
          <i className="fas fa-sign-out-alt mr-2"></i>
          Logout
        </button>
      </div>
    </div>
  );
};

export default ProfileSidebar;