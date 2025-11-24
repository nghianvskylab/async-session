import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    // Ramp up to 1000 RPS over 30 seconds
    { duration: '30s', target: 1000 },
    // Maintain 1000 RPS for 2 minutes
    { duration: '2m', target: 1000 },
    // Ramp down to 0 RPS over 30 seconds
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // 95% of requests must complete below 200ms, 99% below 500ms
    'http_req_duration': ['p(95)<200', 'p(99)<500'],
    // Error rate must be below 1% (only 5xx errors count)
    'errors': ['rate<0.01'],
    // HTTP status should be 200 or 404 (not 5xx)
    'http_req_failed': ['rate<0.01'],
  },
};

// Base URL for the API
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Main test function
export default function () {
  // Random ID from 1 to 10000
  const id = Math.floor(Math.random() * 10000) + 1;
  
  // Make GET request to the user endpoint
  const response = http.get(`${BASE_URL}/users/${id}`);
  
  // Check if the response is successful
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'response has data': (r) => {
      if (r.status === 200) {
        const body = r.json();
        return body && body.id;
      }
      return r.status === 404;
    },
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  // Record errors (only count 5xx errors as failures)
  errorRate.add(response.status >= 500);
  
  // Add a small sleep to prevent overwhelming the server
  // This helps maintain the target RPS while being respectful to the server
  sleep(0.1);
}
