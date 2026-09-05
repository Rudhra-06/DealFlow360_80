/**
 * DealFlow360 — Firebase SDK Initialization
 * Initializes Firebase App and Analytics using configured credentials.
 */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAnalytics, logEvent } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-analytics.js";

const firebaseConfig = {
  apiKey: "AIzaSyCQMQ9teEy9X_4Fe0JpPPKRCCysvY8v89w",
  authDomain: "dealflow360-9bb5c.firebaseapp.com",
  projectId: "dealflow360-9bb5c",
  storageBucket: "dealflow360-9bb5c.firebasestorage.app",
  messagingSenderId: "510730462531",
  appId: "1:510730462531:web:28f1ca48cf4c5445c8bbf6",
  measurementId: "G-N8TXSVSW0K"
};

// Initialize Firebase App
const app = initializeApp(firebaseConfig);

// Initialize Firebase Analytics
let analytics = null;
try {
  analytics = getAnalytics(app);
  console.log("Firebase initialized successfully for DealFlow360 (App ID: 1:510730462531:web:28f1ca48cf4c5445c8bbf6)");
} catch (err) {
  console.warn("Firebase Analytics warning:", err);
}

// Global helper for logging analytics events
window.DealFlowFirebase = {
  app: app,
  analytics: analytics,
  logAnalyticsEvent: function (eventName, eventParams = {}) {
    if (analytics) {
      try {
        logEvent(analytics, eventName, eventParams);
        console.log(`[Firebase Analytics] Event '${eventName}' logged:`, eventParams);
      } catch (err) {
        console.warn("[Firebase Analytics] Error logging event:", err);
      }
    }
  }
};
