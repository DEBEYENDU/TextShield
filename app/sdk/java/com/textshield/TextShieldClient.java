package com.textshield.sdk;

/**
 * Official Java SDK for TextShield v2.1
 * 
 * This SDK provides programmatic access to TextShield's
 * spam/phishing/fraud analysis capabilities.
 */
public class TextShieldClient {
    
    private static final String DEFAULT_BASE_URL = "http://localhost:8000";
    private static final int DEFAULT_TIMEOUT = 30000; // 30 seconds
    
    private final String baseUrl;
    private final String apiKey;
    private final int timeout;
    
    public TextShieldClient() {
        this(DEFAULT_BASE_URL, null);
    }
    
    public TextShieldClient(String baseUrl) {
        this(baseUrl, null);
    }
    
    public TextShieldClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl != null ? baseUrl : DEFAULT_BASE_URL;
        this.apiKey = apiKey;
        this.timeout = DEFAULT_TIMEOUT;
    }
    
    public String getBaseUrl() {
        return baseUrl;
    }
    
    public String getApiKey() {
        return apiKey;
    }
    
    /**
     * Analyze a single message for spam/phishing/fraud.
     * 
     * @param text The message text to analyze
     * @return Analysis result as a map
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> analyze(String text) throws TextShieldException {
        return sendRequest("/analyze", "POST", 
            java.util.Map.of("text", text));
    }
    
    /**
     * Analyze multiple messages asynchronously.
     * 
     * @param texts Array of message texts to analyze
     * @return Job information with jobId
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> batchAnalyze(String[] texts) throws TextShieldException {
        java.util.Map<String, Object> body = new java.util.HashMap<>();
        body.put("texts", java.util.Arrays.asList(texts));
        return sendRequest("/batch", "POST", body);
    }
    
    /**
     * Get analysis history.
     * 
     * @param skip Number of records to skip
     * @param limit Maximum number of records to return
     * @param classification Filter by classification
     * @return History items
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> getHistory(int skip, int limit, String classification) throws TextShieldException {
        java.util.Map<String, Object> params = new java.util.HashMap<>();
        params.put("skip", skip);
        params.put("limit", limit);
        if (classification != null) {
            params.put("classification", classification);
        }
        return sendRequest("/history", "GET", params);
    }
    
    /**
     * Get a specific analysis record by ID.
     * 
     * @param recordId The record ID
     * @return The analysis record
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> getRecord(int recordId) throws TextShieldException {
        return sendRequest("/history/" + recordId, "GET", new java.util.HashMap<>());
    }
    
    /**
     * Delete an analysis record.
     * 
     * @param recordId The record ID to delete
     * @return Deletion confirmation
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> deleteRecord(int recordId) throws TextShieldException {
        return sendRequest("/history/" + recordId, "DELETE", new java.util.HashMap<>());
    }
    
    /**
     * Check system health.
     * 
     * @return Health status
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> healthCheck() throws TextShieldException {
        return sendRequest("/system/health", "GET", new java.util.HashMap<>());
    }
    
    /**
     * Get TextShield version.
     * 
     * @return Version information
     * @throws TextShieldException if the API call fails
     */
    public java.util.Map<String, Object> getVersion() throws TextShieldException {
        return sendRequest("/system/version", "GET", new java.util.HashMap<>());
    }
    
    /**
     * Quick analysis of a message.
     * 
     * @param text Message text to analyze
     * @return Analysis result
     * @throws TextShieldException if the API call fails
     */
    public static java.util.Map<String, Object> quickAnalyze(String text) throws TextShieldException {
        TextShieldClient client = new TextShieldClient();
        try {
            return client.analyze(text);
        } finally {
            client.close();
        }
    }
    
    /**
     * Close any resources.
     */
    public void close() {
        // No persistent resources in current implementation
    }
    
    /**
     * Send HTTP request to the TextShield API.
     * 
     * @param endpoint API endpoint relative to /api/v2
     * @param method HTTP method
     * @param body Request body
     * @return API response as a map
     * @throws TextShieldException if the API call fails
     */
    private java.util.Map<String, Object> sendRequest(String endpoint, String method, java.util.Map<String, Object> body) throws TextShieldException {
        try {
            java.net.URI uri = new java.net.URI(baseUrl + "/api/v2" + endpoint);
            java.net.http.HttpClient client = java.net.http.HttpClient.newBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(timeout / 1000))
                .build();
            
            // Build URL with query parameters if needed
            StringBuilder urlBuilder = new StringBuilder(baseUrl + "/api/v2" + endpoint);
            
            java.net.http.HttpRequest.Builder requestBuilder = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create(urlBuilder.toString()))
                .timeout(java.time.Duration.ofMillis(timeout));
            
            // Set headers
            requestBuilder.header("Content-Type", "application/json");
            if (apiKey != null) {
                requestBuilder.header("X-API-Key", apiKey);
            }
            
            // Set body and method
            if ("POST".equals(method)) {
                requestBuilder.POST(java.net.http.HttpRequest.BodyPublishers.ofString(
                    com.google.gson.GsonBuilder().create().toJson(body)));
            } else if ("GET".equals(method)) {
                requestBuilder.GET();
            }
            
            java.net.http.HttpRequest request = requestBuilder.build();
            
            java.net.http.HttpResponse<String> response = client.send(
                request,
                java.net.http.HttpResponse.BodyHandlers.ofString()
            );
            
            if (response.statusCode() != 200) {
                throw new TextShieldException(
                    "API request failed: " + response.statusCode() + " " + response.body());
            }
            
            // Parse response using Gson
            com.google.gson.JsonElement element = 
                com.google.gson.JsonParser.parseString(response.body());
            
            return com.google.gson.JsonParser.parseString(response.body()).getAsJsonObject().entrySet().stream()
                .collect(java.util.stream.Collectors.toMap(
                    java.util.Map.Entry::getKey,
                    e -> convertJsonElement(e.getValue())
                ));
            
        } catch (java.net.URIMalformedException e) {
            throw new TextShieldException("Invalid URL: " + e.getMessage(), e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new TextShieldException("Request interrupted: " + e.getMessage(), e);
        }
    }
    
    /**
     * Convert a JsonElement to an appropriate Java object.
     * 
     * @param element The JsonElement to convert
     * @return The converted Java object
     */
    private Object convertJsonElement(com.google.gson.JsonElement element) {
        if (element.isJsonNull()) {
            return null;
        } else if (element.isJsonPrimitive()) {
            com.google.gson.JsonPrimitive primitive = element.getAsJsonPrimitive();
            if (primitive.isBoolean()) {
                return primitive.getAsBoolean();
            } else if (primitive.isNumber()) {
                return primitive.getAsNumber();
            } else if (primitive.isString()) {
                return primitive.getAsString();
            }
        } else if (element.isJsonArray()) {
            return element.asList().stream()
                .map(this::convertJsonElement)
                .toList();
        } else if (element.isJsonObject()) {
            return element.entrySet().stream()
                .collect(java.util.stream.Collectors.toMap(
                    java.util.Map.Entry::getKey,
                    e -> convertJsonElement(e.getValue())
                ));
        }
        return element.toString();
    }
    
    /**
     * TextShield-specific exception.
     */
    public static class TextShieldException extends Exception {
        public TextShieldException(String message) {
            super(message);
        }
        
        public TextShieldException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}