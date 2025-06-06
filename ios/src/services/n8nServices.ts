// src/services/n8nServices.ts

export interface N8NResponse {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
}

class N8NService {
  private readonly BASE_URL = "https://samuelpert.app.n8n.cloud";
  private currentSessionId: string | null = null;

  // Generate a unique session ID for the conversation
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Get or create session ID
  private getSessionId(): string {
    if (!this.currentSessionId) {
      this.currentSessionId = this.generateSessionId();
      console.log('[n8nService] Generated new session ID:', this.currentSessionId);
    }
    return this.currentSessionId;
  }

  // Clear session (call this when clearing chat)
  public clearSession(): void {
    this.currentSessionId = null;
    console.log('[n8nService] Session cleared');
  }

  async callWorkflow(
    webhookId: string,
    payload: any,
    method: "GET" | "POST" = "POST"
  ): Promise<N8NResponse> {
    try {
      // Log the outgoing request
      console.log("[n8nService] Calling webhook:", webhookId);
      console.log("[n8nService] Payload:", JSON.stringify(payload, null, 2));
      
      const url = `${this.BASE_URL}/webhook/${webhookId}`;
      console.log("[n8nService] Full URL:", url);

      const requestOptions: RequestInit = {
        method,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      };

      let finalUrl = url;

      if (method === "POST" && payload) {
        requestOptions.body = JSON.stringify(payload);
      } else if (method === "GET" && payload) {
        const queryParams = new URLSearchParams();
        Object.keys(payload).forEach(key => {
          queryParams.append(key, String(payload[key]));
        });
        finalUrl = `${url}?${queryParams.toString()}`;
      }

      console.log("[n8nService] Making request...");
      const response = await fetch(finalUrl, requestOptions);
      const responseText = await response.text();
      
      // Log the response
      console.log("[n8nService] Response status:", response.status);
      console.log("[n8nService] Response text:", responseText);

      if (!response.ok) {
        console.error("[n8nService] Error response:", responseText);
        throw new Error(`N8N webhook error! status: ${response.status}, message: ${responseText}`);
      }

      if (!responseText) {
        return { 
          success: true, 
          message: "Workflow executed successfully (empty response)" 
        };
      }

      let data;
      try {
        data = JSON.parse(responseText);
        console.log("[n8nService] Parsed response data:", JSON.stringify(data, null, 2));
      } catch (parseError) {
        console.log("[n8nService] Response is not JSON, treating as plain text");
        return {
          success: true,
          message: responseText,
          data: { rawResponse: responseText }
        };
      }

      // Extract AI response from n8n workflow data
      let aiResponse = "No AI response found";
      
      // Try different possible response structures
      if (Array.isArray(data) && data.length > 0 && data[0].output) {
        aiResponse = data[0].output;
      } else if (data.output) {
        aiResponse = data.output;
      } else if (data.text) {
        aiResponse = data.text;
      } else if (data.response) {
        aiResponse = data.response;
      } else if (data.message) {
        aiResponse = data.message;
      } else if (data.result) {
        aiResponse = data.result;
      } else if (typeof data === 'string') {
        aiResponse = data;
      }

      console.log("[n8nService] Extracted AI response:", aiResponse);

      return {
        success: true,
        message: aiResponse,
        data: data,
      };
    } catch (error: any) {
      console.error("[n8nService] Error in callWorkflow:", error);
      return {
        success: false,
        error: error.message || "Failed to execute N8N workflow.",
      };
    }
  }

  // Updated to match RoaryChatScreen expectations
  async sendChatMessage(
    message: string,
    workflowId: string = "roary-chat"
  ): Promise<N8NResponse> {
    const sessionId = this.getSessionId();
    
    // Try different payload structures based on what your n8n workflow expects
    const payload = {
      message: message,
      chatInput: message,  // Some n8n workflows expect this
      sessionId: sessionId,
      sessionID: sessionId, // Try both cases
      timestamp: new Date().toISOString(),
      type: "chat"
    };
    
    return this.callWorkflow(workflowId, payload, "POST");
  }

  // Test connection method
  async testConnection(): Promise<boolean> {
    try {
      console.log("[n8nService] Testing connection to:", this.BASE_URL);
      const response = await this.sendChatMessage("Test connection", "roary-chat");
      console.log("[n8nService] Test response:", response);
      return response.success;
    } catch (error) {
      console.error("[n8nService] Connection test failed:", error);
      return false;
    }
  }
}

// Export singleton instance
export const n8nService = new N8NService();