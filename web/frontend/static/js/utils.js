// Utility functions for API calls and error handling

/**
 * Wrapper for fetch API with error handling
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - The response data
 */
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }

        return data;
    } catch (error) {
        if (!options.silent) {
            console.error('API Error:', error);
        }
        throw error;
    }
}

// Export functions
window.fetchWithErrorHandling = fetchWithErrorHandling;