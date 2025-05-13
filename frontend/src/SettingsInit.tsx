import React from 'react';
import ReactDOM from 'react-dom/client';
import Settings from './components/Settings/Settings';

// Store root instances to avoid recreating them
const rootInstances: Record<string, ReactDOM.Root> = {};

// Function to initialize the Settings component in a specified element
export function initSettings(elementId: string) {
  const settingsContainer = document.getElementById(elementId);
  if (!settingsContainer) {
    return false;
  }
  
  // If we already have a root for this container, use it
  if (!rootInstances[elementId]) {
    // Otherwise create a new root
    rootInstances[elementId] = ReactDOM.createRoot(settingsContainer);
  }
  
  // Render the component to the root
  rootInstances[elementId].render(
    <React.StrictMode>
      <Settings />
    </React.StrictMode>
  );
  
  return true;
}

// Expose the initialization function to the window object
declare global {
  interface Window {
    initSettings: (elementId: string) => boolean;
  }
}

window.initSettings = initSettings;