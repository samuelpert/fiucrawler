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
   * Call a specific N8N webhook workflow
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
          Accept: "application/json", // Often good to specify accept header
        },
      };

      if (method === "POST" && payload) {
        requestOptions.body = JSON.stringify(payload);
      }

      const response = await fetch(url, requestOptions);
      const responseText = await response.text(); // Read response text first

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
        // Handle empty response if it's not expected to be an error
        console.warn("N8N webhook returned an empty response.");
        // Depending on your N8N workflow, an empty response might be successful
        // If an empty response for a particular workflow implies success with no data:
        // return { success: true, message: "Workflow executed, empty response received." };
        // Or, if JSON is always expected:
        throw new Error("Received empty response, expected JSON.");
      }

      const data = JSON.parse(responseText); // Parse text to JSON

      return {
        success: true,
        message:
          data.message ||
          data.response ||
          data.output ||
          "Workflow executed successfully",
        data: data,
      };
    } catch (error: any) {
      console.error("N8N Workflow Error in callWorkflow:", error);
      // Check if error is already an N8NResponse-like structure
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
   */
  async sendChatMessage(
    message: string,
    workflowId: string = "roary-chat" // Default workflow ID for chat
  ): Promise<N8NResponse> {
    return this.callWorkflow(workflowId, {
      message,
      timestamp: new Date().toISOString(),
      type: "chat", // Standardized type for chat messages
    });
  }

  /**
   * Execute a specific task workflow
   */
  async executeTask(
    taskType: string,
    parameters: any,
    workflowId: string // Make workflowId required for specific tasks
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
      type: "task", // Standardized type for tasks
    });
  }

  /**
   * Test N8N connection using a generic chat message
   */
  async testConnection(
    testWorkflowId: string = "roary-chat" // Use a common workflow for testing
  ): Promise<boolean> {
    console.log(`Testing N8N connection with workflow: ${testWorkflowId}`);
    try {
      const response = await this.sendChatMessage(
        "N8N connection test message",
        testWorkflowId
      );
      console.log("N8N test connection response:", response);
      return response.success;
    } catch (error) {
      console.error("N8N connection test failed:", error);
      return false;
    }
  }
}

// Pre-configured workflows for common tasks
// Ensure these webhook IDs match the 'Path' in your N8N Webhook nodes
export const N8N_WORKFLOWS = {
  ROARY_CHAT: "roary-chat", // Example: for general chat
  IMPORTANT_DATES: "important-dates",
  PROSPECTIVE_STUDENTS: "prospective-students",
  ALUMNI_SERVICES: "alumni-services",
  SECURITY_TIPS: "security-tips",
  // Add more workflow IDs as needed
};

export const n8nService = new N8NService();
