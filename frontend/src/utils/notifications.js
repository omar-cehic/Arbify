/**
 * Browser Notification Utility for Arbify
 * Handles browser notifications for arbitrage opportunities
 */

// Check if browser supports notifications
export const isNotificationSupported = () => {
  return 'Notification' in window && navigator.serviceWorker;
};

// Request notification permission
export const requestNotificationPermission = async () => {
  if (!isNotificationSupported()) {
    throw new Error('Browser notifications not supported');
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    throw new Error('Notification permission denied');
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
};

// Create arbitrage opportunity notification
export const sendArbitrageNotification = (opportunity) => {
  if (Notification.permission !== 'granted') {
    console.warn('Cannot send notification: Permission not granted');
    return null;
  }

  const title = 'New Arbitrage Opportunity!';
  const body = `${opportunity.match} - ${opportunity.profit_percentage.toFixed(1)}% profit potential`;
  
  const options = {
    body: body,
    icon: '/favicon.svg',
    tag: `arbitrage-${opportunity.id}`,
    requireInteraction: false,
    silent: false
  };

  try {
    const notification = new Notification(title, options);
    
    // Handle notification click
    notification.onclick = () => {
      window.focus();
      window.location.href = '/arbitrage';
      notification.close();
    };

    // Auto close after 8 seconds
    setTimeout(() => {
      notification.close();
    }, 8000);

    return notification;
  } catch (error) {
    console.error('Failed to create notification:', error);
    return null;
  }
};

// Test notification
export const sendTestNotification = () => {
  const testOpportunity = {
    id: 'test-' + Date.now(),
    match: 'Test Match vs Demo Team',
    profit_percentage: 3.2,
    sport_title: 'Football'
  };

  return sendArbitrageNotification(testOpportunity);
};

// Check if user prefers notifications at current time
export const shouldNotifyAtCurrentTime = () => {
  const hour = new Date().getHours();
  // Don't notify between 11 PM and 7 AM (user's likely sleeping)
  return hour >= 7 && hour < 23;
};

// Get notification interval based on subscription
export const getNotificationInterval = (subscriptionTier) => {
  switch (subscriptionTier) {
    case 'premium':
    case 'trial':
      return 40000; // 40 seconds for premium/trial (matches API live updates)
    case 'basic':
      return 60000; // 1 minute for basic
    default:
      return 120000; // 2 minutes for free
  }
};

// Format notification text
export const formatNotificationBody = (opportunity) => {
  const profit = opportunity.profit_percentage.toFixed(1);
  const sport = opportunity.sport_title || 'Sports';
  
  return `${profit}% profit in ${sport}\n${opportunity.home_team} vs ${opportunity.away_team}`;
};

export default {
  isNotificationSupported,
  requestNotificationPermission,
  sendArbitrageNotification,
  sendTestNotification,
  shouldNotifyAtCurrentTime,
  getNotificationInterval,
  formatNotificationBody
};
