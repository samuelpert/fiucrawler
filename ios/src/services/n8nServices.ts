// src/services/n8nService.ts
import { Platform } from 'react-native';

// Environment configuration
const N8N_CONFIG = {
  // For iOS Simulator and Android Emulator
  localhost: "http://localhost:5678",
  
  // For physical devices - UPDATE THIS WITH YOUR NGROK URL
  ngrok: "https://9d37-131-94-186-11.ngrok-free.app",
  
  // For production (when you deploy N8N)
  production: "https://your-production-n8n-url.com"
};

// Function to determine which URL to use
const getN8NBaseUrl = (): string => {
  // Check if we're in development mode
  const isDevelopment = __DEV__;
  
  if (!isDevelopment) {
    // Production mode
    return N8N_CONFIG.production;
  }
  
  // Development mode - detect device type
  if (Platform.OS === 'ios') {
    // For iOS: Check if it's simulator or physical device
    // We can't directly detect this, so we'll try localhost first
    // and fall back to ngrok if needed
    return N8N_CONFIG.localhost;
  } else if (Platform.OS === 'android') {
    // For Android: Similar approach
    return N8N_CONFIG.localhost;
  } else {
    // Web or other platforms
    return N8N_CONFIG.localhost;
  }
};

// Alternative: Manual override for testing
const FORCE_USE_NGROK = true; // Set to true when testing on physical devices

const getActiveN8NUrl = (): string => {
  if (FORCE_USE_NGROK) {
    console.log('🌐 Using ngrok URL for testing:', N8N_CONFIG.ngrok);
    return N8N_CONFIG.ngrok;
  }
  
  const url = getN8NBaseUrl();
  console.log('🔗 Using N8N URL:', url);
  return url;
};

export interface N8NResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
}

export interface N8NWorkflowConfig {
  webhookId: string;
  workflowName: string;
}

class N8NService {
  private baseUrl: string;
  private currentSessionId: string | null = null;

  constructor() {
    this.baseUrl = getActiveN8NUrl();
    console.log('🚀 N8NService initialized with URL:', this.baseUrl);
  }

  // Method to update the base URL (useful for testing)
  public updateBaseUrl(url: string): void {
    this.baseUrl = url;
    console.log('🔄 N8N base URL updated to:', this.baseUrl);
  }

  // Method to switch to ngrok URL
  public useNgrokUrl(): void {
    this.baseUrl = N8N_CONFIG.ngrok;
    console.log('🌐 Switched to ngrok URL:', this.baseUrl);
  }

  // Method to switch to localhost URL
  public useLocalhostUrl(): void {
    this.baseUrl = N8N_CONFIG.localhost;
    console.log('🏠 Switched to localhost URL:', this.baseUrl);
  }

  // Generate a unique session ID for the conversation
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Get or create session ID
  private getSessionId(): string {
    if (!this.currentSessionId) {
      this.currentSessionId = this.generateSessionId();
      console.log('Generated new session ID:', this.currentSessionId);
    }
    return this.currentSessionId;
  }

  // Clear session (call this when clearing chat)
  public clearSession(): void {
    this.currentSessionId = null;
    console.log('Session cleared');
  }

  /**
   * Call a specific N8N webhook workflow with proper query params
   */
  async callWorkflow(
    webhookId: string,
    payload: any,
    method: "GET" | "POST" = "POST"
  ): Promise<N8NResponse> {
    try {
      console.log(
        `🔗 Calling N8N webhook: ${webhookId} with method: ${method}`,
        payload
      );

      const url = `${this.baseUrl}/webhook/${webhookId}`;
      console.log(`📡 Full N8N webhook URL: ${url}`);

      const requestOptions: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      };

      // For POST requests, send data in body
      if (method === "POST" && payload) {
        requestOptions.body = JSON.stringify(payload);
      }

      // For GET requests, add data as query parameters
      let finalUrl = url;
      if (method === "GET" && payload) {
        const queryParams = new URLSearchParams();
        Object.keys(payload).forEach(key => {
          queryParams.append(key, String(payload[key]));
        });
        finalUrl = `${url}?${queryParams.toString()}`;
      }

      console.log(`📤 Making request to: ${finalUrl}`);

      const response = await fetch(finalUrl, requestOptions);
      const responseText = await response.text();

      if (!response.ok) {
        console.error(
          `❌ N8N webhook error! Status: ${response.status}, Response Text:`,
          responseText
        );
        
        // If localhost fails, suggest trying ngrok
        if (this.baseUrl.includes('localhost') && response.status >= 500) {
          console.log('💡 Localhost failed. Try switching to ngrok URL for physical device testing.');
        }
        
        throw new Error(
          `N8N webhook error! status: ${response.status}, message: ${responseText}`
        );
      }

      console.log("✅ Raw N8N webhook response text:", responseText);

      if (!responseText) {
        console.warn("⚠️ N8N webhook returned an empty response.");
        return { 
          success: true, 
          message: "Workflow executed successfully (empty response)" 
        };
      }

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        // If response isn't JSON, treat the text as the message
        console.log("📝 Response is not JSON, treating as plain text");
        return {
          success: true,
          message: responseText,
          data: { rawResponse: responseText }
        };
      }

      // Extract AI response from n8n workflow data
      let aiResponse = "No AI response found";
      
      // Based on your log, the AI response is in data[0].output
      if (Array.isArray(data) && data.length > 0 && data[0].output) {
        aiResponse = data[0].output;
      } else if (data.output) {
        aiResponse = data.output;
      } else if (data.text) {
        aiResponse = data.text;
      } else if (data.response) {
        aiResponse = data.response;
      } else if (data.message && data.message !== "Workflow executed successfully") {
        aiResponse = data.message;
      } else if (data.result) {
        aiResponse = data.result;
      }

      console.log("🤖 Extracted AI response:", aiResponse);
      console.log("📊 Full n8n response data:", JSON.stringify(data, null, 2));

      return {
        success: true,
        message: aiResponse,
        data: data,
      };
    } catch (error: any) {
      console.error("💥 N8N Workflow Error in callWorkflow:", error);
      
      // Enhanced error handling with suggestions
      if (error.message?.includes('Network request failed') || 
          error.message?.includes('ECONNREFUSED') ||
          error.message?.includes('Failed to fetch')) {
        
        const suggestion = this.baseUrl.includes('localhost') 
          ? "Try switching to ngrok URL for physical device testing, or ensure N8N is running on localhost:5678"
          : "Check your internet connection and ensure the ngrok tunnel is active";
          
        return {
          success: false,
          error: `Connection failed: ${error.message}. ${suggestion}`
        };
      }
      
      if (error.success === false && error.error) {
        return error;
      }
      return {
        success: false,
        error: error.message || "Failed to execute N8N workflow. Check console for details.",
      };
    }
  }

  async sendChatMessage(
    message: string,
    workflowId: string = "roary-chat"
  ): Promise<N8NResponse> {
    const sessionId = this.getSessionId();
    
    return this.callWorkflow(workflowId, {
      chatInput: message,
      message,
      sessionId: sessionId,
      timestamp: new Date().toISOString(),
      type: "chat"
    }, "POST");
  }

  // Execute a specific task workflow
  async executeTask(
    taskType: string,
    parameters: any,
    workflowId: string,
    method: "GET" | "POST" = "POST"
  ): Promise<N8NResponse> {
    if (!workflowId) {
      console.error("Workflow ID is required for executeTask");
      return {
        success: false,
        error: "Workflow ID is required for executeTask",
      };
    }
    return this.callWorkflow(workflowId, {
      taskType,
      parameters,
      timestamp: new Date().toISOString(),
      type: "task"
    }, method);
  }

  /**
   * Test N8N connection - tries both GET and POST methods
   */
  async testConnection(
    testWorkflowId: string = "roary-chat"
  ): Promise<boolean> {
    console.log(`🧪 Testing N8N connection with workflow: ${testWorkflowId}`);
    console.log(`🔗 Testing URL: ${this.baseUrl}`);
    
    try {
      // First try GET method
      console.log("Testing with GET method...");
      const getResponse = await this.callWorkflow(testWorkflowId, {
        message: "N8N connection test (GET)",
        test: true
      }, "GET");
      
      if (getResponse.success) {
        console.log("✅ GET method test successful:", getResponse);
        return true;
      }
    } catch (error) {
      console.log("❌ GET method failed, trying POST...");
    }

    try {
      // Then try POST method
      console.log("Testing with POST method...");
      const postResponse = await this.callWorkflow(testWorkflowId, {
        message: "N8N connection test (POST)",
        test: true
      }, "POST");
      
      console.log("✅ POST method test response:", postResponse);
      return postResponse.success;
    } catch (error) {
      console.error("❌ Both GET and POST methods failed:", error);
      return false;
    }
  }

  /**
   * Debug function to see the full n8n response structure
   */
  async debugResponse(
    message: string = "Debug test message",
    workflowId: string = "roary-chat"
  ): Promise<N8NResponse> {
    try {
      const response = await this.callWorkflow(workflowId, {
        chatInput: message,
        message,
        timestamp: new Date().toISOString(),
        type: "debug"
      }, "POST");

      // Log the full structure for debugging
      console.log("=== N8N DEBUG RESPONSE ===");
      console.log("Full response object:", response);
      console.log("Response data:", JSON.stringify(response.data, null, 2));
      console.log("========================");

      return response;
    } catch (error: any) {
      console.error("Debug request failed:", error);
      return {
        success: false,
        error: error.message || "Debug request failed"
      };
    }
  }
}

// Pre-configured workflows for common tasks
export const N8N_WORKFLOWS = {
  ROARY_CHAT: "roary-chat",
  IMPORTANT_DATES: "important-dates", 
  PROSPECTIVE_STUDENTS: "prospective-students",
  ALUMNI_SERVICES: "alumni-services",
  SECURITY_TIPS: "security-tips",
};

export const n8nService = new N8NService();