/**
 * Notification Service for Arbify
 * Handles polling for new arbitrage opportunities and sending notifications
 * Updated: 2026-02-02
 */

import axios from 'axios';
import { sendArbitrageNotification, shouldNotifyAtCurrentTime, getNotificationInterval } from '../utils/notifications';

// Helper to normalize bookmaker names for comparison
const normalizeBookmakerName = (name) => {
  if (!name) return '';
  return name.toLowerCase().replace(/[^a-z0-9]/g, '');
};

const extractBookmakerNames = (opportunity) => {
  const names = new Set();

  // Strategy 1: 'best_odds' object
  if (opportunity.best_odds) {
    Object.values(opportunity.best_odds).forEach(outcome => {
      if (outcome && outcome.bookmaker) {
        names.add(normalizeBookmakerName(outcome.bookmaker));
      }
    });
  }

  // Strategy 2: 'bookmakers' array of strings
  if (Array.isArray(opportunity.bookmakers)) {
    opportunity.bookmakers.forEach(bm => {
      if (typeof bm === 'string') names.add(normalizeBookmakerName(bm));
      else if (bm.title) names.add(normalizeBookmakerName(bm.title)); // Object structure
    });
  }

  return Array.from(names);
};

class NotificationService {
  constructor() {
    this.pollingInterval = null;
    this.lastNotificationTime = {};
    this.isPolling = false;
  }

  // Start polling for arbitrage opportunities
  startPolling(userPreferences) {
    if (this.isPolling) {
      console.log('Notification polling already active');
      return;
    }

    if (!userPreferences.notification_browser) {
      console.log('Browser notifications disabled by user');
      return;
    }

    if (Notification.permission !== 'granted') {
      console.log('Notification permission not granted');
      return;
    }

    const subscriptionTier = userPreferences.subscriptionTier || localStorage.getItem('subscription_tier') || 'basic';
    const intervalMs = getNotificationInterval(subscriptionTier);

    console.log(`🔔 Starting notification polling every ${intervalMs / 1000} seconds for ${subscriptionTier} tier`);

    this.isPolling = true;
    this.pollingInterval = setInterval(() => {
      this.checkForOpportunities(userPreferences);
    }, intervalMs);

    // Also check immediately
    this.checkForOpportunities(userPreferences);
  }

  // Stop polling
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      this.isPolling = false;
      console.log('Notification polling stopped');
    }
  }

  // Check for new arbitrage opportunities
  async checkForOpportunities(userPreferences) {
    try {
      // Don't notify during sleeping hours
      if (!shouldNotifyAtCurrentTime()) {
        return;
      }

      console.log('Checking for arbitrage opportunities...');

      // Fetch current arbitrage opportunities from SGO API
      // Use cache (force_refresh=false) to be efficient
      const response = await axios.get('/api/arbitrage/sgo', {
        params: {
          live_only: false,
          min_profit: userPreferences.minimum_profit_threshold || 1.0,
          force_refresh: false
        },
        timeout: 15000
      });

      if (response.data && response.data.arbitrage_opportunities && response.data.arbitrage_opportunities.length > 0) {
        // Map SGO format to expected format if needed, or add 'match' property
        const opportunities = response.data.arbitrage_opportunities.map(opp => ({
          ...opp,
          match: `${opp.home_team} vs ${opp.away_team}`
        }));
        this.processOpportunities(opportunities, userPreferences);
      }
    } catch (error) {
      // Only log significant errors, not 404s or network timeouts
      if (error.response && error.response.status !== 404) {
        console.error('Error checking for opportunities:', error.message);
      }
    }
  }

  // Process opportunities and send notifications
  processOpportunities(opportunities, userPreferences) {
    // 1. Filter opportunities that meet criteria and haven't been notified recently
    const notifyingOpportunities = opportunities.filter(opp =>
      this.shouldNotifyForOpportunity(opp, userPreferences)
    );

    if (notifyingOpportunities.length === 0) {
      return;
    }

    // 2. Sort by profit percentage (descending) to find the best one
    notifyingOpportunities.sort((a, b) => b.profit_percentage - a.profit_percentage);

    // 3. Notify only about the SINGLE best opportunity
    const bestOpportunity = notifyingOpportunities[0];
    this.sendNotificationForOpportunity(bestOpportunity);

    // Log if we skipped others
    if (notifyingOpportunities.length > 1) {
      console.log(`🔔 Notified about best opportunity (${bestOpportunity.profit_percentage}%), skipped ${notifyingOpportunities.length - 1} others.`);
    }
  }

  // Check if we should notify for this specific opportunity
  // Check if we should notify for this specific opportunity
  shouldNotifyForOpportunity(opportunity, userPreferences) {
    // 1. Check profit threshold
    if (opportunity.profit_percentage < userPreferences.minimum_profit_threshold) {
      return false;
    }

    // 2. Check sports preference
    if (userPreferences.preferred_sports && userPreferences.preferred_sports.length > 0) {
      if (!userPreferences.preferred_sports.includes(opportunity.sport_key)) {
        return false;
      }
    }

    // 3. Exact Match Bookmaker Logic
    // Only notify if ALL bookmakers involved in the arbitrage are in the user's preferred list
    if (userPreferences.preferred_bookmakers && userPreferences.preferred_bookmakers.length > 0) {
      const opportunityBookmakers = extractBookmakerNames(opportunity);

      // Normalize user preferences for comparison
      const userPreferredSet = new Set(
        userPreferences.preferred_bookmakers.map(bm => normalizeBookmakerName(bm))
      );

      // Check if every bookmaker in this opportunity is preferred
      const allBookmakersPreferred = opportunityBookmakers.every(bm => userPreferredSet.has(bm));

      if (!allBookmakersPreferred) {
        // console.log('Skipping opportunity - bookmaker mismatch', opportunityBookmakers);
        return false;
      }
    }

    // Prevent duplicate notifications (same opportunity within 30 minutes)
    const notificationKey = `${opportunity.home_team}-${opportunity.away_team}-${opportunity.sport_key}`;
    const lastNotified = this.lastNotificationTime[notificationKey];
    const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);

    if (lastNotified && lastNotified > thirtyMinutesAgo) {
      return false;
    }

    return true;
  }

  // Send notification for opportunity
  sendNotificationForOpportunity(opportunity) {
    const notificationKey = `${opportunity.home_team}-${opportunity.away_team}-${opportunity.sport_key}`;

    try {
      const notification = sendArbitrageNotification(opportunity);

      if (notification) {
        // Record that we sent this notification
        this.lastNotificationTime[notificationKey] = Date.now();

        console.log(`Sent notification for: ${opportunity.home_team} vs ${opportunity.away_team} (${opportunity.profit_percentage.toFixed(1)}% profit)`);

        // Clean up old notification times (older than 2 hours)
        this.cleanupOldNotificationTimes();
      }
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  }

  // Clean up old notification times to prevent memory leaks
  cleanupOldNotificationTimes() {
    const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000);

    Object.keys(this.lastNotificationTime).forEach(key => {
      if (this.lastNotificationTime[key] < twoHoursAgo) {
        delete this.lastNotificationTime[key];
      }
    });
  }

  // Update user preferences and restart polling if needed
  updatePreferences(newPreferences) {
    const wasPolling = this.isPolling;

    if (wasPolling) {
      this.stopPolling();
    }

    if (newPreferences.notification_browser) {
      this.startPolling(newPreferences);
    }
  }

  // Get current polling status
  getStatus() {
    return {
      isPolling: this.isPolling,
      intervalMs: this.pollingInterval ? getNotificationInterval(localStorage.getItem('subscription_tier') || 'basic') : null,
      lastNotificationCount: Object.keys(this.lastNotificationTime).length
    };
  }
}

// Create singleton instance
const notificationService = new NotificationService();

export default notificationService;
