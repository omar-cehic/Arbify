import * as Sentry from "@sentry/react";

const isProduction = import.meta.env.PROD;
const sentryDsn = import.meta.env.VITE_SENTRY_DSN || "https://0770a1ac594012beb41b26dcad2ed076@o4509956621139968.ingest.us.sentry.io/4509956649582592";

export const initSentry = () => {
  if (!sentryDsn) {
    if (isProduction) console.warn("VITE_SENTRY_DSN missing");
    return;
  }

  Sentry.init({
    dsn: sentryDsn,
    environment: isProduction ? "production" : "development",
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
    ],
    tracesSampleRate: isProduction ? 0.2 : 1.0,
    replaysSessionSampleRate: isProduction ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0,
  });
  console.log("Sentry initialized (frontend)");
};

export default Sentry;
