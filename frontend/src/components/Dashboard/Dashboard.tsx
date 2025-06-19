import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

// Mock data type definitions
interface WeeklyData {
  day: string;
  normal: number;
  injection: number;
}

interface DashboardData {
  totalMessages: number;
  normalMessages: number;
  injectionMessages: number;
  weeklyData: WeeklyData[];
}

const Dashboard: React.FC = () => {
  // State for dashboard data
  const [data, setData] = useState<DashboardData>({
    totalMessages: 1247,
    normalMessages: 1189,
    injectionMessages: 58,
    weeklyData: [
      { day: 'Mon', normal: 48, injection: 4 },
      { day: 'Tue', normal: 36, injection: 6 },
      { day: 'Wed', normal: 60, injection: 8 },
      { day: 'Thu', normal: 40, injection: 2 },
      { day: 'Fri', normal: 52, injection: 5 },
      { day: 'Sat', normal: 24, injection: 1 },
      { day: 'Sun', normal: 20, injection: 1 }
    ]
  });

  // Calculate percentages
  const totalPercent = (data.normalMessages / data.totalMessages) * 100;
  const injectionPercent = (data.injectionMessages / data.totalMessages) * 100;

  // Initialize dashboard data when component mounts
  useEffect(() => {
    // In the future, this could fetch real data from an API
    // For now, we're using the mock data initialized in the state
    
    // You could add an API call here, for example:
    // async function fetchDashboardData() {
    //   try {
    //     const response = await fetch('/api/v1/dashboard/stats');
    //     const apiData = await response.json();
    //     setData(apiData);
    //   } catch (error) {
    //     console.error('Error fetching dashboard data:', error);
    //   }
    // }
    // fetchDashboardData();
    
    // Check server status
    fetch('http://localhost:8000/api/health')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(statusData => {
        const serverStatusElement = document.getElementById('serverStatus');
        if (serverStatusElement) {
          serverStatusElement.textContent = `Server Status: ${statusData.status || 'Online'}`;
        }
      })
      .catch(error => {
        console.error('Error checking server status:', error);
        const serverStatusElement = document.getElementById('serverStatus');
        if (serverStatusElement) {
          serverStatusElement.textContent = `Server Status: Error - ${error.message}`;
        }
      });
  }, []);

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
      <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
      
      {/* Top row with stats and pie chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        {/* Total Messages Stat */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Messages</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="text-4xl sm:text-5xl lg:text-6xl font-bold text-primary leading-none" id="total-messages-count">
                {data.totalMessages.toLocaleString()}
              </div>
              <div className="flex items-center text-green-500 font-medium text-xs sm:text-sm">
                <svg className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                </svg>
                <span>12.5% increase from last month</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Pie Chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Message Types</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
          <div className="w-full h-48 sm:h-56 lg:h-64 flex items-center justify-center" id="pie-chart-container">
            <div className="text-center">
              <div className="w-32 h-32 rounded-full mx-auto mb-4 relative" style={{background: `conic-gradient(#3b82f6 0deg ${totalPercent * 3.6}deg, #ef4444 ${totalPercent * 3.6}deg 360deg)`}}>
                <div className="absolute inset-4 bg-card rounded-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-lg font-bold">{totalPercent.toFixed(1)}%</div>
                    <div className="text-xs text-muted-foreground">Normal</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
              <span className="text-xs sm:text-sm text-muted-foreground">Normal ({totalPercent.toFixed(1)}%)</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
              <span className="text-xs sm:text-sm text-muted-foreground">Injections ({injectionPercent.toFixed(1)}%)</span>
            </div>
          </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Bottom row with weekly chart */}
      <Card className="w-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">Messages Last Week</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
        <div className="w-full h-48 sm:h-56 lg:h-64">
          <div className="h-full flex items-end justify-between gap-2 px-4">
            {data.weeklyData.map((dayData, index) => (
              <div key={index} className="flex flex-col items-center flex-1">
                <div className="w-full flex flex-col items-center">
                  <div 
                    className="w-8 bg-blue-500 rounded-t mb-1" 
                    style={{ height: `${Math.max(dayData.normal * 2, 8)}px` }}
                    title={`${dayData.normal} normal messages`}
                  ></div>
                  <div 
                    className="w-8 bg-red-500 rounded-b" 
                    style={{ height: `${Math.max(dayData.injection * 8, 4)}px` }}
                    title={`${dayData.injection} potential injections`}
                  ></div>
                </div>
                <span className="text-xs mt-2 text-muted-foreground">{dayData.day}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex flex-wrap justify-center gap-4 mt-4">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 mr-2 rounded"></div>
            <span className="text-xs sm:text-sm text-muted-foreground">Normal Messages</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 mr-2 rounded"></div>
            <span className="text-xs sm:text-sm text-muted-foreground">Potential Injections</span>
          </div>
        </div>
        
        <p id="serverStatus" className="text-muted-foreground mt-2 text-xs sm:text-sm text-center">Server Status: Online</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;