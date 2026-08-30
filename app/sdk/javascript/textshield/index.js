/**
 * Official JavaScript SDK for TextShield v2.1
 * Works in Node.js and browser environments.
 */

const fetch = require('node-fetch');

const DEFAULT_BASE_URL = 'http://localhost:8000';

/**
 * TextShieldClient - Main SDK class
 */
class TextShieldClient {
  /**
   * @param {Object} options
   * @param {string} options.baseUrl - Base URL of the TextShield API
   * @param {string} options.apiKey - API key for authentication
   * @param {number} [options.timeout=30000] - Request timeout in milliseconds
   */
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || DEFAULT_BASE_URL;
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      this.defaultHeaders['X-API-Key'] = this.apiKey;
    }
  }

  /**
   * Make an HTTP request to the TextShield API
   * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
   * @param {string} endpoint - API endpoint (relative to /api/v2)
   * @param {Object} [body] - Request body for POST/PUT
   * @param {Object} [query] - Query parameters
   * @returns {Promise<Object>} API response
   * @private
   */
  async _request(method, endpoint, body = null, query = {}) {
    const url = new URL(`/api/v2${endpoint}`, this.baseUrl);
    
    // Add query parameters
    Object.entries(query).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });

    const options = {
      method,
      headers: this.defaultHeaders,
      timeout: this.timeout,
    };

    if (body !== null) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `API request failed: ${response.status} ${response.statusText} - ${errorBody}`
      );
    }

    return response.json();
  }

  /**
   * Analyze a single message for spam/phishing/fraud
   * @param {string} text - The message text to analyze
   * @param {boolean} [includeExplanation=true] - Whether to include explanation
   * @returns {Promise<Object>} Analysis result
   */
  async analyze(text, includeExplanation = true) {
    return this._request('POST', '/analyze', {
      text,
      include_explanation: includeExplanation,
    });
  }

  /**
   * Analyze multiple messages asynchronously
   * @param {string[]} texts - Array of message texts to analyze
   * @returns {Promise<Object>} Job information with job_id
   */
  async batchAnalyze(texts) {
    return this._request('POST', '/batch', {
      texts,
    });
  }

  /**
   * Get analysis history
   * @param {Object} [options] - Pagination and filter options
   * @param {number} [options.skip=0] - Number of records to skip
   * @param {number} [options.limit=50] - Maximum number of records to return
   * @param {string} [options.classification] - Filter by classification
   * @returns {Promise<Object>} History items
   */
  async getHistory(options = {}) {
    const { skip = 0, limit = 50, classification } = options;
    return this._request('GET', '/history', null, { skip, limit, classification });
  }

  /**
   * Get a specific analysis record by ID
   * @param {number} recordId - The record ID
   * @returns {Promise<Object>} The analysis record
   */
  async getRecord(recordId) {
    return this._request('GET', `/history/${recordId}`);
  }

  /**
   * Delete an analysis record
   * @param {number} recordId - The record ID to delete
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteRecord(recordId) {
    return this._request('DELETE', `/history/${recordId}`);
  }

  /**
   * Check system health
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    return this._request('GET', '/system/health');
  }

  /**
   * Get TextShield version
   * @returns {Promise<Object>} Version information
   */
  async getVersion() {
    return this._request('GET', '/system/version');
  }

  /**
   * Close any open resources
   */
  dispose() {
    // No persistent resources to close in browser version
  }
}

/**
 * Quick analysis function
 * @param {string} text - Message text to analyze
 * @param {string} apiKey - API key for authentication
 * @param {string} [baseUrl='http://localhost:8000'] - Base API URL
 * @returns {Promise<Object>} Analysis result
 */
async function quickAnalyze(text, apiKey, baseUrl = DEFAULT_BASE_URL) {
  const client = new TextShieldClient({ baseUrl, apiKey });
  try {
    return await client.analyze(text);
  } finally {
    client.dispose();
  }
}

module.exports = {
  TextShieldClient,
  quickAnalyze,
};