import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { API_URL } from '../../config/api';

interface ProjectToken {
  token_id: number;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  last_used_at: string | null;
  created_by_username: string;
}

interface ProjectTokenList {
  tokens: ProjectToken[];
  project_id: number;
  project_name: string;
}

const Settings: React.FC = () => {
  const [token, setToken] = useState<string>('');
  const [tokenDisplay, setTokenDisplay] = useState<boolean>(false);
  const [projectTokens, setProjectTokens] = useState<ProjectToken[]>([]);
  const [projectInfo, setProjectInfo] = useState<{ id: number; name: string } | null>(null);
  const [notifications, setNotifications] = useState<boolean>(false);
  const [darkMode, setDarkMode] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  useEffect(() => {
    // Check if dark mode is already enabled
    const isDark = document.documentElement.classList.contains('dark');
    const savedTheme = localStorage.getItem('theme');
    setDarkMode(isDark || savedTheme === 'dark');

    // Load existing project tokens
    loadProjectTokens();
  }, []);

  const loadProjectTokens = async () => {
    const authToken = localStorage.getItem('token');
    if (!authToken) return;

    try {
      const response = await fetch(`${API_URL}/tokens/projects/tokens`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const data: ProjectTokenList = await response.json();
        setProjectTokens(data.tokens);
        setProjectInfo({ id: data.project_id, name: data.project_name });
      }
    } catch (error) {
      console.error('Error loading project tokens:', error);
    }
  };
  
  const toggleDarkMode = (enabled: boolean) => {
    setDarkMode(enabled);
    const root = document.documentElement;
    
    if (enabled) {
      root.classList.add('dark');
      root.classList.remove('light');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const generateProjectToken = async () => {
    const authToken = localStorage.getItem('token');
    if (!authToken) {
      alert('You must be logged in to generate a project API token');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/tokens/projects/tokens`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to generate project token');
      }

      const data = await response.json();

      // Display the new token
      setToken(data.token);
      setTokenDisplay(true);

      // Reload the token list
      await loadProjectTokens();
    } catch (error) {
      console.error('Error generating project token:', error);
      alert('Error generating project token. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const revokeProjectToken = async (tokenId: number) => {
    const authToken = localStorage.getItem('token');
    if (!authToken) return;

    if (!confirm('Are you sure you want to revoke this token? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/tokens/projects/tokens/${tokenId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        // Reload the token list
        await loadProjectTokens();
        alert('Token revoked successfully');
      } else {
        throw new Error('Failed to revoke token');
      }
    } catch (error) {
      console.error('Error revoking token:', error);
      alert('Error revoking token. Please try again.');
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
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="notifications" className="text-sm font-medium">Enable notifications</label>
            <input 
              type="checkbox" 
              id="notifications" 
              className="h-4 w-4 rounded border-input bg-background text-primary focus:ring-2 focus:ring-primary"
              checked={notifications}
              onChange={e => setNotifications(e.target.checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <label htmlFor="darkmode" className="text-sm font-medium">Dark mode</label>
            <input 
              type="checkbox" 
              id="darkmode" 
              className="h-4 w-4 rounded border-input bg-background text-primary focus:ring-2 focus:ring-primary"
              checked={darkMode}
              onChange={e => toggleDarkMode(e.target.checked)}
            />
          </div>
        </div>
        </CardContent>
      </Card>
      
      {/* Project API Access Section */}
      <Card>
        <CardHeader>
          <CardTitle>Project API Access</CardTitle>
          {projectInfo && (
            <p className="text-sm text-muted-foreground">
              Project: <strong>{projectInfo.name}</strong> (ID: {projectInfo.id})
            </p>
          )}
        </CardHeader>
        <CardContent>
        <p className="text-muted-foreground mb-4">Generate project API tokens to access the ML-Checker API programmatically. These tokens are shared among all users in your project.</p>

        <div id="api-token-section">
          <button
            onClick={generateProjectToken}
            disabled={isLoading}
            className="auth-btn bg-blue-600 hover:bg-blue-700 mb-4 disabled:opacity-50"
          >
            {isLoading ? 'Generating...' : 'Generate New Project API Token'}
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
API_URL = "http://localhost:8000/api/v1"

# Set up authorization header
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# Create a new message
response = requests.post(
    f"{API_URL}/chat/messages",
    headers=headers,
    json={
        "content": "Hello from API!",
        "session_id": "my_session_123"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Message created with ID: {data['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
`}
                </pre>
              </div>
            </div>
          )}

          {/* Existing Project Tokens */}
          {projectTokens.length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium mb-3">Existing Project Tokens</h4>
              <div className="space-y-3">
                {projectTokens.map((token) => (
                  <div key={token.token_id} className="bg-gray-50 p-4 rounded-lg border">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium">Token #{token.token_id}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            token.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {token.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </div>
                        <div className="text-xs text-gray-600 space-y-1">
                          <p>Created: {new Date(token.created_at).toLocaleString()}</p>
                          <p>Created by: {token.created_by_username}</p>
                          {token.last_used_at && (
                            <p>Last used: {new Date(token.last_used_at).toLocaleString()}</p>
                          )}
                          {token.expires_at && (
                            <p>Expires: {new Date(token.expires_at).toLocaleString()}</p>
                          )}
                        </div>
                      </div>
                      {token.is_active && (
                        <button
                          onClick={() => revokeProjectToken(token.token_id)}
                          className="ml-4 px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;