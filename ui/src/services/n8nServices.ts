// src/services/n8nService.ts
const N8N_BASE_URL = "http://localhost:5678"; // Ensure this is correct for your environment

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

  constructor() {
    this.baseUrl = N8N_BASE_URL;
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
        `Calling N8N webhook: ${webhookId} with method: ${method}`,
        payload
      );

      const url = `${this.baseUrl}/webhook/${webhookId}`;
      console.log(`Full N8N webhook URL: ${url}`);

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

      console.log(`Making request to: ${finalUrl}`);

      const response = await fetch(finalUrl, requestOptions);
      const responseText = await response.text();

      if (!response.ok) {
        console.error(
          `N8N webhook error! Status: ${response.status}, Response Text:`,
          responseText
        );
        throw new Error(
          `N8N webhook error! status: ${response.status}, message: ${responseText}`
        );
      }

      console.log("Raw N8N webhook response text:", responseText);

      if (!responseText) {
        console.warn("N8N webhook returned an empty response.");
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
        console.log("Response is not JSON, treating as plain text");
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

      console.log("Extracted AI response:", aiResponse);
      console.log("Full n8n response data:", JSON.stringify(data, null, 2));

      return {
        success: true,
        message: aiResponse,
        data: data,
      };
    } catch (error: any) {
      console.error("N8N Workflow Error in callWorkflow:", error);
      if (error.success === false && error.error) {
        return error;
      }
      return {
        success: false,
        error: error.message || "Failed to execute N8N workflow. Check console for details.",
      };
    }
  }

  /**
   * Send a chat message to N8N workflow
   * Uses POST method with chatInput field that AI Agent expects
   */
  async sendChatMessage(
    message: string,
    workflowId: string = "roary-chat"
  ): Promise<N8NResponse> {
    // Send as POST request with chatInput field for AI Agent
    return this.callWorkflow(workflowId, {
      chatInput: message,  // AI Agent expects this field name
      message,             // Keep original for compatibility
      timestamp: new Date().toISOString(),
      type: "chat"
    }, "POST");
  }

  /**
   * Send a chat message using POST method (alternative)
   */
  async sendChatMessagePOST(
    message: string,
    workflowId: string = "roary-chat"
  ): Promise<N8NResponse> {
    return this.callWorkflow(workflowId, {
      message,
      timestamp: new Date().toISOString(),
      type: "chat"
    }, "POST");
  }

  /**
   * Execute a specific task workflow
   */
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
    console.log(`Testing N8N connection with workflow: ${testWorkflowId}`);
    
    try {
      // First try GET method
      console.log("Testing with GET method...");
      const getResponse = await this.callWorkflow(testWorkflowId, {
        message: "N8N connection test (GET)",
        test: true
      }, "GET");
      
      if (getResponse.success) {
        console.log("GET method test successful:", getResponse);
        return true;
      }
    } catch (error) {
      console.log("GET method failed, trying POST...");
    }

    try {
      // Then try POST method
      console.log("Testing with POST method...");
      const postResponse = await this.callWorkflow(testWorkflowId, {
        message: "N8N connection test (POST)",
        test: true
      }, "POST");
      
      console.log("POST method test response:", postResponse);
      return postResponse.success;
    } catch (error) {
      console.error("Both GET and POST methods failed:", error);
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