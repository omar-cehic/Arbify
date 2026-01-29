import ReactGA from 'react-ga4';

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;

export const initAnalytics = () => {
    if (GA_MEASUREMENT_ID) {
        ReactGA.initialize(GA_MEASUREMENT_ID);
        console.log('📊 Google Analytics initialized');
    } else {
        console.log('ℹ️ Google Analytics not configured (VITE_GA_MEASUREMENT_ID missing)');
    }
};

export const logPageView = (path) => {
    if (GA_MEASUREMENT_ID) {
        ReactGA.send({ hitType: "pageview", page: path });
    }
};
