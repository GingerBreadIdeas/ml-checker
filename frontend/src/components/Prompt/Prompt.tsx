import React, { useState, useEffect } from 'react';

interface PromptCheckForm {
  prompt_text: string;
  model_id: string;
  model_supplier: string;
  probe: string;
  project_id: number;
}

interface PromptTest {
  id: number;
  created_at: string;
  content: {
    probe: string;
    model_id: string;
    model_supplier: string;
    prompt: string;
  };
  checked: boolean;
  check_results?: any;
}

const Prompt: React.FC = () => {
  const [activeTab, setActiveTab] = useState('tests');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<PromptCheckForm>({
    prompt_text: '',
    model_id: 'deepseek-r1:1.5b',
    model_supplier: 'ollama',
    probe: 'promptinject.HijackHateHumansMini',
    project_id: 1
  });
  const [promptTests, setPromptTests] = useState<PromptTest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [expandedPrompts, setExpandedPrompts] = useState<Set<number>>(new Set());
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Fetch prompt tests
  const fetchPromptTests = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/prompt-check?project_id=1`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPromptTests(data.prompts || []);
      } else {
        console.error('Failed to fetch prompt tests');
      }
    } catch (error) {
      console.error('Error fetching prompt tests:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load tests when switching to tests tab
  useEffect(() => {
    if (activeTab === 'tests') {
      fetchPromptTests();
    }
  }, [activeTab]);

  const toggleExpanded = (id: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const togglePromptExpanded = (id: number) => {
    const newExpanded = new Set(expandedPrompts);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedPrompts(newExpanded);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Analyze test results to determine if tests passed or failed
  const analyzeTestResults = (test: PromptTest) => {
    if (!test.checked || !test.check_results) {
      return { status: 'pending', color: 'bg-gray-400', passed: 0, total: 0 };
    }

    try {
      // Parse the results if it's a string
      let results = test.check_results;
      if (typeof results === 'string') {
        results = JSON.parse(results);
      }

      // Look for evaluation entries in the raw_results
      let totalPassed = 0;
      let totalTests = 0;
      let hasResults = false;

      if (results.raw_results) {
        const lines = results.raw_results.split('\n');
        for (const line of lines) {
          if (line.trim()) {
            try {
              const entry = JSON.parse(line);
              if (entry.entry_type === 'eval') {
                hasResults = true;
                totalPassed += entry.passed || 0;
                totalTests += entry.total || 0;
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        }
      }

      if (!hasResults) {
        return { status: 'unknown', color: 'bg-yellow-500', passed: 0, total: 0 };
      }

      const allPassed = totalPassed === totalTests;
      return {
        status: allPassed ? 'passed' : 'failed',
        color: allPassed ? 'bg-green-500' : 'bg-red-500',
        passed: totalPassed,
        total: totalTests
      };
    } catch (e) {
      return { status: 'error', color: 'bg-yellow-500', passed: 0, total: 0 };
    }
  };

  // Download report function
  const downloadReport = (test: PromptTest) => {
    if (!test.check_results) return;

    const dataStr = JSON.stringify(test.check_results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `test_report_${test.id}_${test.content.probe}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

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
      const response = await fetch(`${import.meta.env.VITE_API_URL}/prompt-check`, {
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
        // Show success message
        setSuccessMessage('Prompt check submitted successfully! Check the Tests tab to monitor progress.');
        setErrorMessage(null);
        // Auto-hide success message after 5 seconds
        setTimeout(() => setSuccessMessage(null), 5000);
        // Refresh tests list if on tests tab
        if (activeTab === 'tests') {
          fetchPromptTests();
        }
      } else {
        throw new Error('Failed to submit prompt check');
      }
    } catch (error) {
      console.error('Error submitting prompt check:', error);
      setErrorMessage('Error submitting prompt check. Please try again.');
      setSuccessMessage(null);
      // Auto-hide error message after 5 seconds
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const clearForm = () => {
    setFormData({
      prompt_text: '',
      model_id: 'deepseek-r1:1.5b',
      model_supplier: 'ollama',
      probe: 'promptinject.HijackHateHumansMini',
      project_id: 1
    });
  };

  // Delete prompt test function
  const deletePromptTest = async (testId: number) => {
    if (!confirm('Are you sure you want to delete this test? This action cannot be undone.')) {
      return;
    }

    setDeletingId(testId);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/prompt-check/${testId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSuccessMessage('Test deleted successfully!');
        setErrorMessage(null);
        // Remove the test from the local state
        setPromptTests(prev => prev.filter(test => test.id !== testId));
        // Auto-hide success message after 3 seconds
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        throw new Error('Failed to delete test');
      }
    } catch (error) {
      console.error('Error deleting test:', error);
      setErrorMessage('Error deleting test. Please try again.');
      setSuccessMessage(null);
      // Auto-hide error message after 5 seconds
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Prompt Testing</h1>
      
      {/* Success/Error Message Bar */}
      {(successMessage || errorMessage) && (
        <div className={`mb-4 p-3 rounded-md flex items-center justify-between ${
          successMessage ? 'bg-green-100 border border-green-400 text-green-700' : 'bg-red-100 border border-red-400 text-red-700'
        }`}>
          <div className="flex items-center">
            <i className={`fas ${successMessage ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2`}></i>
            <span>{successMessage || errorMessage}</span>
          </div>
          <button
            onClick={() => {
              setSuccessMessage(null);
              setErrorMessage(null);
            }}
            className="text-current hover:opacity-75"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}
      
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
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={clearForm}
                    className="px-3 py-1 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Clear
                  </button>
                </div>
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
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Tests</h2>
              <button
                onClick={fetchPromptTests}
                disabled={isLoading}
                className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400 text-sm"
              >
                <i className="fas fa-sync-alt mr-1"></i>
                {isLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>
            
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="text-gray-500">Loading tests...</div>
              </div>
            ) : promptTests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No prompt tests found. Create one in the Prepare tab.
              </div>
            ) : (
              <div className="space-y-3">
                {promptTests.map((test) => {
                  const testResult = analyzeTestResults(test);
                  return (
                    <div key={test.id} className="border border-gray-200 rounded-lg overflow-hidden">
                      {/* Clickable header */}
                      <div 
                        onClick={() => toggleExpanded(test.id)}
                        className="p-4 bg-white hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-4">
                          {/* Status indicator */}
                          <div className="flex items-center">
                            <div className={`w-3 h-3 ${testResult.color} rounded-full mr-2`}></div>
                          </div>
                          
                          {/* Test info */}
                          <div>
                            <div className="font-medium text-gray-900">
                              {test.content.probe}
                            </div>
                            <div className="text-sm text-gray-500">
                              {formatDate(test.created_at)} • Model: {test.content.model_id}
                              {test.checked && testResult.total > 0 && (
                                <span className="ml-2">• {testResult.passed}/{testResult.total} passed</span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {/* Action buttons */}
                        <div className="flex items-center space-x-2">
                          {/* Delete button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deletePromptTest(test.id);
                            }}
                            disabled={deletingId === test.id}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Delete test"
                          >
                            {deletingId === test.id ? (
                              <i className="fas fa-spinner fa-spin"></i>
                            ) : (
                              <i className="fas fa-trash"></i>
                            )}
                          </button>
                          
                          {/* Expand/collapse icon */}
                          <div className="text-gray-400">
                            <i className={`fas fa-chevron-${expandedItems.has(test.id) ? 'up' : 'down'}`}></i>
                          </div>
                        </div>
                      </div>
                      
                      {/* Expandable content */}
                      {expandedItems.has(test.id) && (
                        <div className="p-4 bg-gray-50 border-t border-gray-200">
                          {test.checked && test.check_results ? (
                            <div className="space-y-3">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-900">Test Report</h4>
                                <div className="flex space-x-2">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      // Pre-fill form with test data and switch to prepare tab
                                      setFormData({
                                        prompt_text: test.content.prompt || '',
                                        model_id: test.content.model_id || 'deepseek-r1:1.5b',
                                        model_supplier: test.content.model_supplier || 'ollama',
                                        probe: test.content.probe || 'promptinject.HijackHateHumansMini',
                                        project_id: 1
                                      });
                                      setActiveTab('prepare');
                                    }}
                                    className="px-3 py-1 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm flex items-center"
                                    title="Edit and retry this test"
                                  >
                                    <i className="fas fa-edit mr-1"></i>
                                    Retry
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      downloadReport(test);
                                    }}
                                    className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                                  >
                                    <i className="fas fa-download mr-1"></i>
                                    Download Report
                                  </button>
                                </div>
                              </div>
                              
                              <div className="bg-white p-3 rounded border">
                                <div className="text-sm">
                                  <span className="font-medium">Status:</span>
                                  <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                                    testResult.status === 'passed' ? 'bg-green-100 text-green-800' :
                                    testResult.status === 'failed' ? 'bg-red-100 text-red-800' :
                                    'bg-yellow-100 text-yellow-800'
                                  }`}>
                                    {testResult.status.charAt(0).toUpperCase() + testResult.status.slice(1)}
                                  </span>
                                  {testResult.total > 0 && (
                                    <span className="ml-2 text-gray-600">
                                      ({testResult.passed}/{testResult.total} tests passed)
                                    </span>
                                  )}
                                </div>
                                
                                <div className="mt-2 text-sm text-gray-600">
                                  <span className="font-medium">Probe:</span> {test.content.probe}
                                </div>
                                <div className="text-sm text-gray-600">
                                  <span className="font-medium">Model:</span> {test.content.model_supplier} / {test.content.model_id}
                                </div>
                              </div>

                              {/* Prompt section */}
                              <div className="bg-white p-3 rounded border">
                                <div 
                                  className="flex items-center justify-between cursor-pointer"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    togglePromptExpanded(test.id);
                                  }}
                                >
                                  <h5 className="font-medium text-gray-900">Prompt Used</h5>
                                  <div className="text-gray-400">
                                    <i className={`fas fa-chevron-${expandedPrompts.has(test.id) ? 'up' : 'down'}`}></i>
                                  </div>
                                </div>
                                {expandedPrompts.has(test.id) && (
                                  <div className="mt-2 bg-gray-50 p-2 rounded text-sm font-mono max-h-32 overflow-y-auto">
                                    {test.content.prompt || 'No prompt available'}
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="text-gray-600">
                              {test.checked ? 'No results available' : 'Test still running...'}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Prompt;
