import React, { useEffect, useState } from 'react';
import { API_BASE } from '../../config/api';

declare global {
  interface Window {
    Bokeh: any;
  }
}

const Anomaly: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [empty, setEmpty] = useState<boolean>(false);
  const [error, setError] = useState<{ isError: boolean; message: string }>({
    isError: false,
    message: '',
  });
  
  // Cache for embedding visualization data
  const [embeddingDataCache, setEmbeddingDataCache] = useState<any>(null);
  const [embeddingLastFetched, setEmbeddingLastFetched] = useState<number | null>(null);
  const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
  
  // Load embedding visualization data
  const loadEmbeddingVisualization = (forceRefresh = false) => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoading(false);
      setEmpty(true);
      return;
    }
    
    // Check if we have cached data and it's still valid
    const now = new Date().getTime();
    if (
      !forceRefresh &&
      embeddingDataCache &&
      embeddingLastFetched &&
      now - embeddingLastFetched < CACHE_DURATION
    ) {
      console.log("Using cached embedding visualization data");
      
      // Use the cached data
      displayEmbeddingData(embeddingDataCache);
      return;
    }
    
    // Show loading state
    setLoading(true);
    setEmpty(false);
    setError({ isError: false, message: '' });
    
    // Fetch embedding data as JSON
    fetch(`${API_BASE}/api/v1/visualization/message_embeddings_json`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(`Failed to fetch embedding data: ${response.status}`);
      }
    })
    .then(data => {
      console.log("Received Bokeh JSON data:", data);
      
      // Update cache with new data
      setEmbeddingDataCache(data);
      setEmbeddingLastFetched(now);
      
      // Display the data
      displayEmbeddingData(data);
    })
    .catch(error => {
      console.error("Error loading embedding data:", error);
      setLoading(false);
      setError({
        isError: true,
        message: error.message
      });
    });
  };
  
  // Helper function to display embedding data
  const displayEmbeddingData = (data: any) => {
    // Hide loading state
    setLoading(false);
    
    // Check for error response
    if (data.status === "error") {
      setError({
        isError: true,
        message: data.message || "Error loading visualization"
      });
      return;
    }
    
    // Check for empty response
    if (data.status === "empty") {
      setEmpty(true);
      return;
    }
    
    // Clear previous visualization
    const embeddingPlot = document.getElementById('embedding-plot');
    if (embeddingPlot) {
      embeddingPlot.innerHTML = '';
    }
    
    try {
      // Properly embed Bokeh using json_item as per documentation
      window.Bokeh.embed.embed_item(data, "embedding-plot");
    } catch (error: any) {
      console.error("Error rendering Bokeh visualization:", error);
      setError({
        isError: true,
        message: `Error rendering visualization: ${error.message}`
      });
    }
  };
  
  // Load visualization when component mounts
  useEffect(() => {
    loadEmbeddingVisualization();
  }, []);
  
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Anomaly Detection</h2>
      
      {/* Visualization Container */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6 w-full">
        <div className="flex justify-between items-center mb-4 w-full">
          <h3 className="text-lg font-medium">Message Embeddings Visualization</h3>
          <button 
            id="refresh-embeddings" 
            className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
            onClick={() => loadEmbeddingVisualization(true)}
          >
            <i className="fas fa-sync-alt mr-1"></i> Refresh
          </button>
        </div>
        
        <p className="text-gray-700 mb-4">This visualization shows text embeddings in 2D space using t-SNE dimensionality reduction. Regular messages are shown in blue, and potential prompt injections in red.</p>
        
        {/* Loading indicator */}
        {loading && (
          <div id="embeddings-loading" className="py-20 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {/* Empty state */}
        {!loading && empty && (
          <div id="embeddings-empty" className="py-20 text-center">
            <p className="text-gray-500">No messages found</p>
            <p className="text-gray-400 text-sm mt-2">Create some messages via the API first</p>
          </div>
        )}
        
        {/* Error state */}
        {!loading && error.isError && (
          <div id="embeddings-error" className="py-20 text-center">
            <p className="text-red-500">Error loading visualization</p>
            <p id="embeddings-error-message" className="text-gray-500 text-sm mt-2">{error.message}</p>
            <button 
              id="embeddings-try-again" 
              className="mt-4 bg-red-100 text-red-700 px-4 py-2 rounded hover:bg-red-200"
              onClick={() => loadEmbeddingVisualization(true)}
            >
              Try Again
            </button>
          </div>
        )}
        
        {/* Bokeh container */}
        {!loading && !empty && !error.isError && (
          <div id="bokeh-container" className="w-full">
            {/* Plot and table will be rendered here */}
            <div id="embedding-plot" className="mt-2 w-full"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Anomaly;