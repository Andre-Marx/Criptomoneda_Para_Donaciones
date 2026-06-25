const configuredApiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5050';

function browserIsLocal() {
  if (typeof window === 'undefined') {
    return false;
  }

  return ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
}

function normalizeApiBaseUrl(apiBaseUrl) {
  if (!browserIsLocal()) {
    return apiBaseUrl;
  }

  try {
    const parsedUrl = new URL(apiBaseUrl);

    if (!['localhost', '127.0.0.1', '::1'].includes(parsedUrl.hostname)) {
      parsedUrl.hostname = window.location.hostname;
      return parsedUrl.toString().replace(/\/$/, '');
    }
  } catch (error) {
    return apiBaseUrl;
  }

  return apiBaseUrl;
}

const API_BASE_URL = normalizeApiBaseUrl(configuredApiBaseUrl);
const NANOSECONDS_PY = 1;
const MICROSECONDS_PY = 1000 * NANOSECONDS_PY;
const MILLISECONDS_PY = 1000 * MICROSECONDS_PY;

const MILLISECONDS_JS = 1;
const SECONDS_JS = MILLISECONDS_JS * 1000;


export {API_BASE_URL, MILLISECONDS_PY, SECONDS_JS};
