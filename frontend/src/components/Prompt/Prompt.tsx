import React, { useState } from 'react';

interface PromptCheckForm {
  prompt_text: string;
  model_id: string;
  model_supplier: string;
  probe: string;
}

const Prompt: React.FC = () => {
  const [activeTab, setActiveTab] = useState('tests');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<PromptCheckForm>({
    prompt_text: '',
    model_id: 'deepseek-r1:1.5b',
    model_supplier: 'ollama',
    probe: 'promptinject.HijackHateHumansMini'
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/prompt_check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Prompt check submitted:', result);
        // Reset form
        setFormData({
          prompt_text: '',
          model_id: 'deepseek-r1:1.5b',
          model_supplier: 'ollama',
          probe: 'promptinject.HijackHateHumansMini'
        });
        alert('Prompt check submitted successfully!');
      } else {
        throw new Error('Failed to submit prompt check');
      }
    } catch (error) {
      console.error('Error submitting prompt check:', error);
      alert('Error submitting prompt check. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Prompt Testing</h1>
      
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('prepare')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'prepare'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Prepare
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tests'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tests
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'prepare' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Prepare Prompt Check</h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Prompt Text */}
              <div>
                <label htmlFor="prompt_text" className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Text
                </label>
                <textarea
                  id="prompt_text"
                  name="prompt_text"
                  value={formData.prompt_text}
                  onChange={handleInputChange}
                  required
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your prompt text here..."
                />
              </div>

              {/* Model Supplier */}
              <div>
                <label htmlFor="model_supplier" className="block text-sm font-medium text-gray-700 mb-2">
                  Model Supplier
                </label>
                <select
                  id="model_supplier"
                  name="model_supplier"
                  value={formData.model_supplier}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="ollama">Ollama</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>

              {/* Model ID */}
              <div>
                <label htmlFor="model_id" className="block text-sm font-medium text-gray-700 mb-2">
                  Model ID
                </label>
                <select
                  id="model_id"
                  name="model_id"
                  value={formData.model_id}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="deepseek-r1:1.5b">deepseek-r1:1.5b</option>
                  <option value="llama3.2:3b">llama3.2:3b</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="claude-3-haiku">claude-3-haiku</option>
                </select>
              </div>

              {/* Probe */}
              <div>
                <label htmlFor="probe" className="block text-sm font-medium text-gray-700 mb-2">
                  Probe
                </label>
                <select
                  id="probe"
                  name="probe"
                  value={formData.probe}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="encoding.InjectBase32">encoding.InjectBase32</option>
                  <option value="promptinject.HijackHateHumansMini">promptinject.HijackHateHumansMini</option>
                  <option value="dan.DAN_Jailbreak">dan.DAN_Jailbreak</option>
                  <option value="grandma.Substances">grandma.Substances</option>
                  <option value="malwaregen.Evasion">malwaregen.Evasion</option>
                </select>
              </div>

              {/* Submit Button */}
              <div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Prompt Check'}
                </button>
              </div>
            </form>
          </div>
        )}
        
        {activeTab === 'tests' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Tests</h2>
            <p className="text-gray-600">View and run your prompt tests here.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Prompt;
