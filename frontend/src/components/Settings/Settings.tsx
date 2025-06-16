import React, { useState, useEffect } from 'react';

const Settings: React.FC = () => {
  const [token, setToken] = useState<string>('');
  const [tokenDisplay, setTokenDisplay] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<boolean>(false);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  const generateToken = async () => {
    const authToken = localStorage.getItem('token');
    if (!authToken) {
      alert('You must be logged in to generate an API token');
      return;
    }
    
    // Hardcoded for Docker environment
    const apiBaseUrl = 'http://localhost:8000';
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/generate-api-token`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate token');
      }
      
      const data = await response.json();
      
      // Display the token
      setToken(data.access_token);
      setTokenDisplay(true);
    } catch (error) {
      console.error('Error generating token:', error);
      alert('Error generating token. Please try again.');
    }
  };

  const copyToken = () => {
    navigator.clipboard.writeText(token);
    alert('Token copied to clipboard');
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Settings</h2>
      
      {/* Preferences Section */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="font-medium text-lg mb-4">Preferences</h3>
        <div className="space-y-2">
          <div className="flex items-center">
            <input 
              type="checkbox" 
              id="notifications" 
              className="mr-2"
              checked={notifications}
              onChange={e => setNotifications(e.target.checked)}
            />
            <label htmlFor="notifications">Enable notifications</label>
          </div>
          <div className="flex items-center">
            <input 
              type="checkbox" 
              id="darkmode" 
              className="mr-2"
              checked={darkMode}
              onChange={e => setDarkMode(e.target.checked)}
            />
            <label htmlFor="darkmode">Dark mode</label>
          </div>
        </div>
      </div>
      
      {/* API Access Section */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="font-medium text-lg mb-4">API Access</h3>
        <p className="text-gray-700 mb-4">Generate an API token to access the ML-Checker API programmatically. This token will expire after 30 days.</p>
        
        <div id="api-token-section">
          <button 
            onClick={generateToken}
            className="auth-btn bg-blue-600 hover:bg-blue-700 mb-4"
          >
            Generate New API Token
          </button>
          
          {tokenDisplay && (
            <div>
              <div className="bg-gray-100 p-4 rounded-lg mb-4">
                <h4 className="font-medium mb-2">Your API Token</h4>
                <p className="text-xs text-gray-500 mb-2">Keep this token secure and don't share it with others.</p>
                <div className="relative">
                  <input 
                    type="text" 
                    readOnly 
                    className="auth-input pr-20 font-mono text-xs" 
                    value={token}
                  />
                  <button 
                    onClick={copyToken}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 text-white px-2 py-1 rounded text-xs"
                  >
                    Copy
                  </button>
                </div>
              </div>
              
              <div className="bg-gray-100 p-4 rounded-lg mb-4">
                <h4 className="font-medium mb-2">Python Example</h4>
                <pre className="bg-gray-800 text-gray-200 p-3 rounded-lg text-xs overflow-x-auto">
{`import requests

# API configuration
API_TOKEN = "${token}"
API_URL = "http://backend:8000/api/v1"

# Set up authorization header
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Get your username
response = requests.get(
    f"{API_URL}/api/whoami", 
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Authenticated as: {data['username']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
`}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;