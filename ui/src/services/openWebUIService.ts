// src/services/openWebUIService.ts
const OPENWEBUI_BASE_URL = 'http://localhost:3000';

export interface ChatResponse {
  success: boolean;
  message?: string;
  error?: string;
}

class OpenWebUIService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = OPENWEBUI_BASE_URL;
  }

  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      console.log('Sending message to OpenWebUI:', message);

      const response = await fetch(`${this.baseUrl}/api/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'llama3.2', // Adjust this to your model
          messages: [
            {
              role: 'user',
              content: message
            }
          ],
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        success: true,
        message: data.choices?.[0]?.message?.content || 'No response received'
      };

    } catch (error: any) {
      console.error('OpenWebUI Error:', error);
      return {
        success: false,
        error: error.message || 'Failed to connect to OpenWebUI'
      };
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/models`);
      return response.ok;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }
}

export const openWebUIService = new OpenWebUIService();