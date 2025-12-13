import React from 'react';
import { MessagesTable, Message } from '../table/messages-table';
import { Card } from '../ui/card';
import { API_URL } from '../../config/api';

const Tracking: React.FC = () => {
  // Delete message handler
  const handleDeleteMessage = async (messageId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/chat/messages/${messageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete message');
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      alert('Error deleting message. Please try again.');
    }
  };

  // Update message's prompt injection status
  const handleUpdateInjectionStatus = async (messageId: string, isPromptInjection: boolean) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/chat/messages/${messageId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_prompt_injection: isPromptInjection
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update message');
      }
    } catch (error) {
      console.error('Error updating message:', error);
      alert('Error updating message. Please try again.');
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-6">
      {/* Messages Table */}
      <MessagesTable
        onDeleteMessage={handleDeleteMessage}
        onUpdateInjectionStatus={handleUpdateInjectionStatus}
      />
      
      {/* API Hint */}
      <Card className="bg-blue-50 border border-blue-200 p-4 text-blue-800">
        <div className="flex">
          <div className="flex-shrink-0 mr-3">
            <i className="fas fa-info-circle text-blue-500 text-xl"></i>
          </div>
          <div>
            <h4 className="font-medium mb-1">Using the Messages API</h4>
            <p className="text-sm">Messages are created via the API using your project API token. All users in a project share the same API tokens. Visit the Settings page to generate a project token and see examples.</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Tracking;