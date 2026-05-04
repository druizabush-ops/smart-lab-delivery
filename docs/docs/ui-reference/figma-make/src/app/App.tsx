import { useState } from 'react';
import { Test } from './Test';
import { LoginScreen } from './screens/LoginScreen';
import { HomeScreen } from './screens/HomeScreen';
import { ResultsListScreen } from './screens/ResultsListScreen';
import { ResultDetailsScreen } from './screens/ResultDetailsScreen';
import { PDFViewerScreen } from './screens/PDFViewerScreen';
import { AppointmentScreen } from './screens/AppointmentScreen';
import { PromotionsScreen } from './screens/PromotionsScreen';
import { ServicesScreen } from './screens/ServicesScreen';

type Screen =
  | 'login'
  | 'home'
  | 'results'
  | 'result-details'
  | 'pdf-viewer'
  | 'appointment'
  | 'promotions'
  | 'services';

type ActiveTab = 'home' | 'results' | 'appointment' | 'promotions' | 'services';

export default function App() {

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [selectedResultId, setSelectedResultId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<ActiveTab>('home');
  const [navigationHistory, setNavigationHistory] = useState<Screen[]>([]);

  const handleLogin = () => {
    setIsAuthenticated(true);
    setCurrentScreen('home');
  };

  const handleNavigate = (screen: Screen, resultId?: string) => {
    setNavigationHistory([...navigationHistory, currentScreen]);
    setCurrentScreen(screen);
    if (resultId) {
      setSelectedResultId(resultId);
    }
  };

  const handleBack = () => {
    if (navigationHistory.length > 0) {
      const previousScreen = navigationHistory[navigationHistory.length - 1];
      setNavigationHistory(navigationHistory.slice(0, -1));
      setCurrentScreen(previousScreen);
    } else {
      setCurrentScreen('home');
      setActiveTab('home');
    }
  };

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    setNavigationHistory([]);

    switch (tab) {
      case 'home':
        setCurrentScreen('home');
        break;
      case 'results':
        setCurrentScreen('results');
        break;
      case 'appointment':
        setCurrentScreen('appointment');
        break;
      case 'promotions':
        setCurrentScreen('promotions');
        break;
      case 'services':
        setCurrentScreen('services');
        break;
    }
  };

  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-[#F8FAFB] w-full max-w-[390px] mx-auto">
      {currentScreen === 'home' && (
        <HomeScreen
          onNavigate={handleNavigate}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'results' && (
        <ResultsListScreen
          onNavigate={handleNavigate}
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'result-details' && (
        <ResultDetailsScreen
          resultId={selectedResultId}
          onNavigate={handleNavigate}
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'pdf-viewer' && (
        <PDFViewerScreen
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'appointment' && (
        <AppointmentScreen
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'promotions' && (
        <PromotionsScreen
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}

      {currentScreen === 'services' && (
        <ServicesScreen
          onBack={handleBack}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      )}
    </div>
  );
}