// src/screens/RoaryChatScreen.tsx
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  useColorScheme,
  Dimensions,
  Image,
  Alert,
} from "react-native";
import { n8nService } from "../services/n8nServices";

const { width } = Dimensions.get("window");

// Sample suggested prompts - now with N8N workflow IDs
const SUGGESTED_PROMPTS = [
  {
    id: 1,
    title: "Important Dates",
    subtitle: "When does fall start?",
    workflowId: "important-dates",
  },
  {
    id: 2,
    title: "Prospective Students",
    subtitle: "What is the application deadline?",
    workflowId: "prospective-students",
  },
  {
    id: 3,
    title: "Alumni",
    subtitle: "How do I get in touch with my old classmates?",
    workflowId: "alumni-services",
  },
  {
    id: 4,
    title: "Security Tips",
    subtitle: "How can I browse safely?",
    workflowId: "security-tips",
  },
];

export const RoaryChatScreen: React.FC = () => {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<
    Array<{ id: string; text: string; isUser: boolean; timestamp: Date }>
  >([]);
  const [loading, setLoading] = useState(false);
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  // Dynamic styles based on theme
  const themeStyles = {
    container: {
      backgroundColor: isDark ? "#1a1a1a" : "#ffffff",
    },
    text: {
      color: isDark ? "#ffffff" : "#000000",
    },
    subtitleText: {
      color: isDark ? "#a0a0a0" : "#666666",
    },
    card: {
      backgroundColor: isDark ? "#2a2a2a" : "#f5f5f5",
      borderColor: isDark ? "#3a3a3a" : "#e0e0e0",
    },
    input: {
      backgroundColor: isDark ? "#2a2a2a" : "#f8f8f8",
      color: isDark ? "#ffffff" : "#000000",
      borderColor: isDark ? "#3a3a3a" : "#e0e0e0",
    },
  };

  const handlePromptPress = async (prompt: (typeof SUGGESTED_PROMPTS)[0]) => {
    const message = prompt.title + " " + prompt.subtitle;
    setInputText(message);

    // Call N8N workflow
    try {
      const response = await n8nService.callWorkflow(prompt.workflowId, {
        message,
      });

      if (response.success) {
        Alert.alert("N8N Response", response.message || "Success!");
      } else {
        Alert.alert("N8N Error", response.error || "Something went wrong");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to connect to N8N");
      console.error("N8N Error:", error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    // Call N8N with the input message
    try {
      const response = await n8nService.sendChatMessage(inputText.trim());

      if (response.success) {
        Alert.alert(
          "N8N Response",
          response.message || "Message sent successfully!"
        );
        setInputText(""); // Clear input after successful send
      } else {
        Alert.alert("N8N Error", response.error || "Failed to send message");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to connect to N8N");
      console.error("N8N Error:", error);
    }
  };

  // Test N8N connection function
  const testN8NConnection = async () => {
    const isConnected = await n8nService.testConnection();
    Alert.alert(
      "N8N Connection Test",
      isConnected
        ? "✅ Connected to N8N!"
        : "❌ Cannot connect to N8N. Make sure it's running on localhost:5678"
    );
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Section */}
        <View style={styles.header}>
          {/* Logo placeholder - we'll add an actual logo later */}
          <View style={styles.logo}>
            <Image
              source={require("../../assets/images/roary-logo.png")}
              style={styles.logoImage}
            />
          </View>

          <Text style={[styles.title, themeStyles.text]}>Roary</Text>
          <Text style={[styles.subtitle, themeStyles.subtitleText]}>
            How can I help you today?
          </Text>

          {/* Test N8N Button - only show when no messages */}
          {messages.length === 0 && (
            <TouchableOpacity
              style={styles.testButton}
              onPress={testN8NConnection}
            >
              <Text style={styles.testButtonText}>Test N8N Connection</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Messages Section - Show when there are messages */}
        {messages.length > 0 && (
          <View style={styles.messagesContainer}>
            <ScrollView
              style={styles.messagesList}
              showsVerticalScrollIndicator={false}
            >
              {messages.map((message) => (
                <View
                  key={message.id}
                  style={[
                    styles.messageBubble,
                    message.isUser ? styles.userBubble : styles.aiBubble,
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      message.isUser ? styles.userText : themeStyles.text,
                    ]}
                  >
                    {message.text}
                  </Text>
                  <Text
                    style={[
                      styles.timestamp,
                      message.isUser
                        ? styles.userTimestamp
                        : themeStyles.subtitleText,
                    ]}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </Text>
                </View>
              ))}
              {loading && (
                <View style={styles.loadingContainer}>
                  <Text style={[styles.loadingText, themeStyles.subtitleText]}>
                    Roary is thinking...
                  </Text>
                </View>
              )}
            </ScrollView>
          </View>
        )}

        {/* Suggested Prompts Section - Show when no messages */}
        {messages.length === 0 && (
          <View style={styles.suggestionsContainer}>
            <Text style={[styles.sectionTitle, themeStyles.subtitleText]}>
              ✨ Suggested
            </Text>

            <View style={styles.promptsGrid}>
              {SUGGESTED_PROMPTS.map((prompt) => (
                <TouchableOpacity
                  key={prompt.id}
                  style={[styles.promptCard, themeStyles.card]}
                  onPress={() => handlePromptPress(prompt)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.promptTitle, themeStyles.text]}>
                    {prompt.title}
                  </Text>
                  <Text
                    style={[styles.promptSubtitle, themeStyles.subtitleText]}
                  >
                    {prompt.subtitle}
                  </Text>

                  {/* Arrow icon */}
                  <View style={styles.promptIcon}>
                    <Text style={[styles.arrowIcon, themeStyles.subtitleText]}>
                      ↗
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Input Section - Fixed at bottom */}
      <View style={[styles.inputContainer, themeStyles.card]}>
        <View style={[styles.inputWrapper, themeStyles.input]}>
          <TextInput
            style={[styles.textInput, themeStyles.input]}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Send a Message"
            placeholderTextColor={isDark ? "#666666" : "#999999"}
            multiline
          />

          {/* Icons */}
          <View style={styles.inputIcons}>
            <TouchableOpacity
              style={[styles.iconButton, loading && styles.sendButtonDisabled]}
              onPress={handleSendMessage}
              disabled={loading}
            >
              <Text style={[styles.icon, themeStyles.subtitleText]}>
                {loading ? "..." : "↑"}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bottom disclaimer */}
        <Text style={[styles.disclaimer, themeStyles.subtitleText]}>
          LLMs can make mistakes. Verify important information.
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
  },

  // Header Styles
  header: {
    alignItems: "center",
    paddingTop: 60,
    paddingBottom: 40,
  },
  logo: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 20,
  },
  logoImage: {
    width: 50,
    height: 50,
    resizeMode: "contain",
  },
  logoText: {
    fontSize: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    textAlign: "center",
  },

  // Test button - minimal styling
  testButton: {
    backgroundColor: "#007AFF",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginTop: 16,
  },
  testButtonText: {
    color: "#fff",
    fontSize: 12,
  },

  // Messages
  messagesContainer: {
    flex: 1,
    paddingBottom: 100, // Space for input area
  },
  messagesList: {
    flex: 1,
  },
  messageBubble: {
    maxWidth: "85%",
    padding: 14,
    borderRadius: 18,
    marginVertical: 4,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#007AFF",
    marginLeft: 60,
  },
  aiBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#f0f0f0",
    marginRight: 60,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: "#fff",
  },
  timestamp: {
    fontSize: 11,
    marginTop: 4,
    opacity: 0.7,
  },
  userTimestamp: {
    color: "rgba(255, 255, 255, 0.7)",
  },
  loadingContainer: {
    alignItems: "center",
    padding: 16,
  },
  loadingText: {
    fontStyle: "italic",
  },

  // Suggestions Styles
  suggestionsContainer: {
    flex: 1,
    paddingBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 16,
    marginLeft: 4,
  },
  promptsGrid: {
    gap: 12,
  },
  promptCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    position: "relative",
    // Shadow for iOS
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    // Shadow for Android
    elevation: 2,
  },
  promptTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
  },
  promptSubtitle: {
    fontSize: 14,
    lineHeight: 20,
  },
  promptIcon: {
    position: "absolute",
    top: 16,
    right: 16,
  },
  arrowIcon: {
    fontSize: 16,
  },

  // Input Styles
  inputContainer: {
    padding: 16,
    borderRadius: 30,
    borderTopWidth: 0,
    paddingBottom: 30,
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "transparent",
  },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 30,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 8,
    minHeight: 48,
  },
  inputPrefix: {
    fontSize: 18,
    marginRight: 12,
    marginBottom: 2,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    maxHeight: 100,
    paddingTop: 0,
    paddingBottom: 0,
  },
  inputIcons: {
    flexDirection: "row",
    marginLeft: 8,
  },
  iconButton: {
    padding: 8,
    marginLeft: 4,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  icon: {
    fontSize: 16,
  },
  disclaimer: {
    fontSize: 12,
    textAlign: "center",
    marginTop: 4,
  },
});
