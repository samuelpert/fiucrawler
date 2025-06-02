// src/screens/RoaryChatScreen.tsx
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  useColorScheme,
  Dimensions,
  Image,
  Alert,
  Platform,
} from "react-native";
import Markdown from "react-native-markdown-display";
import { n8nService } from "../services/n8nServices";

const { width } = Dimensions.get("window");

// Sample suggested prompts - now with N8N workflow IDs
const SUGGESTED_PROMPTS = [
  {
    id: 1,
    title: "Important Dates",
    subtitle: "When does fall start?",
    workflowId: "roary-chat",
  },
  {
    id: 2,
    title: "Prospective Students",
    subtitle: "What is the application deadline?",
    workflowId: "roary-chat",
  },
  {
    id: 3,
    title: "Alumni",
    subtitle: "How do I get in touch with my old classmates?",
    workflowId: "roary-chat",
  },
  {
    id: 4,
    title: "Security Tips",
    subtitle: "How can I browse safely?",
    workflowId: "roary-chat",
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

  // Markdown styles for AI messages - Fixed with black text for light AI bubbles
  const markdownStyles = {
    body: {
      fontSize: 16,
      lineHeight: 22,
      color: "#000000", // Always black text for AI messages
    },
    heading1: {
      fontSize: 24,
      fontWeight: "bold" as "bold",
      marginBottom: 8,
      color: "#000000", // Always black text
    },
    heading2: {
      fontSize: 20,
      fontWeight: "bold" as "bold",
      marginBottom: 6,
      color: "#000000", // Always black text
    },
    heading3: {
      fontSize: 18,
      fontWeight: "bold" as "bold",
      marginBottom: 4,
      color: "#000000", // Always black text
    },
    strong: {
      fontWeight: "bold" as "bold",
      color: "#000000", // Always black text for bold
    },
    link: {
      color: "#007AFF", // Standard link blue
      textDecorationLine: "underline" as "underline",
    },
    list_item: {
      marginBottom: 4,
      color: "#000000", // Always black text for list items
    },
    bullet_list: {
      marginBottom: 8,
    },
    ordered_list: {
      marginBottom: 8,
    },
  };

  const addMessage = (text: string, isUser: boolean) => {
    const newMessage = {
      id: Date.now().toString(),
      text,
      isUser,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  // Clear Chat function with confirmation dialog
  const clearChat = () => {
    Alert.alert(
      "Clear Chat",
      "Are you sure you want to clear the chat? This action cannot be undone.",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Clear",
          style: "destructive",
          onPress: () => {
            setMessages([]);
            console.log("Chat cleared");
          },
        },
      ]
    );
  };

  const handlePromptPress = async (prompt: (typeof SUGGESTED_PROMPTS)[0]) => {
    const message = prompt.subtitle; // Use the subtitle as the actual message
    setInputText(message);

    // Add user message to chat
    addMessage(message, true);
    setLoading(true);

    try {
      const response = await n8nService.sendChatMessage(
        message,
        prompt.workflowId
      );

      if (response.success) {
        // Extract the actual AI response
        let aiMessage = response.message || "No response from AI";

        console.log("Full N8N Response:", response);
        console.log("AI Message:", aiMessage);

        addMessage(aiMessage, false);
        setInputText("");
      } else {
        addMessage(`Error: ${response.error || "Something went wrong"}`, false);
      }
    } catch (error) {
      console.error("Prompt Error:", error);
      addMessage("Error: Failed to connect to N8N", false);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const messageText = inputText.trim();
    addMessage(messageText, true);
    setInputText("");
    setLoading(true);

    try {
      // Try GET method first, then POST if it fails
      let response = await n8nService.sendChatMessage(messageText);

      if (!response.success) {
        console.log("GET failed, trying POST method...");
        response = await n8nService.sendChatMessage(messageText);
      }

      if (response.success) {
        // Extract the actual AI response
        let aiMessage = response.message || "No response from AI";

        // Log the full response for debugging
        console.log("Full N8N Response:", response);
        console.log("AI Message:", aiMessage);

        addMessage(aiMessage, false);
      } else {
        addMessage(
          `Error: ${response.error || "Failed to send message"}`,
          false
        );
      }
    } catch (error) {
      console.error("Send Message Error:", error);
      addMessage("Error: Failed to connect to N8N", false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]}>
      {/* Background Image */}
      <Image
        source={require("../../assets/images/fiu-motto.png")}
        style={styles.backgroundImage}
        resizeMode="contain"
      />

      <KeyboardAvoidingView
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header Section */}
          <View style={styles.header}>
            {/* Clear Chat Button - Only show when there are messages */}
            {messages.length > 0 && (
              <TouchableOpacity
                style={styles.clearButton}
                onPress={clearChat}
                disabled={loading}
              >
                <Text style={styles.clearButtonIcon}>🗑️</Text>
              </TouchableOpacity>
            )}

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
                    {message.isUser ? (
                      <Text style={[styles.messageText, styles.userText]}>
                        {message.text}
                      </Text>
                    ) : (
                      <Markdown style={markdownStyles}>{message.text}</Markdown>
                    )}
                    <Text
                      style={[
                        styles.timestamp,
                        message.isUser
                          ? styles.userTimestamp
                          : styles.aiTimestamp, // Fixed: specific style for AI timestamps
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
                    <Text
                      style={[styles.loadingText, themeStyles.subtitleText]}
                    >
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
                    style={[
                      styles.promptCard,
                      themeStyles.card,
                      loading && styles.promptCardDisabled,
                    ]}
                    onPress={() => handlePromptPress(prompt)}
                    activeOpacity={0.7}
                    disabled={loading}
                  >
                    <Text style={[styles.promptTitle, themeStyles.text]}>
                      {prompt.title}
                    </Text>
                    <Text
                      style={[styles.promptSubtitle, themeStyles.subtitleText]}
                    >
                      {prompt.subtitle}
                    </Text>

                    <View style={styles.promptIcon}>
                      <Text
                        style={[styles.arrowIcon, themeStyles.subtitleText]}
                      >
                        ↗
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}
        </ScrollView>

        {/* Input Section - Now outside ScrollView but inside KeyboardAvoidingView */}
        <View style={[styles.inputContainer, themeStyles.card]}>
          <View style={[styles.inputWrapper, themeStyles.input]}>
            <TextInput
              style={[styles.textInput, themeStyles.input]}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Send a Message"
              placeholderTextColor={isDark ? "#666666" : "#999999"}
              multiline
              editable={!loading}
            />

            <View style={styles.inputIcons}>
              <TouchableOpacity
                style={[
                  styles.iconButton,
                  loading && styles.sendButtonDisabled,
                ]}
                onPress={handleSendMessage}
                disabled={loading || !inputText.trim()}
              >
                <Text style={[styles.icon, themeStyles.subtitleText]}>
                  {loading ? "..." : "↑"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <Text style={[styles.disclaimer, themeStyles.subtitleText]}>
            LLMs can make mistakes. Verify important information.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 120, // Add padding to account for input area
  },

  // Background Image
  backgroundImage: {
    position: "absolute",
    top: "50%",
    left: "50%",
    width: width * 0.8, // 80% of screen width
    height: width * 0.8, // Keep it square, adjust as needed
    transform: [
      { translateX: -(width * 0.4) }, // Half of width to center
      { translateY: -(width * 0.3) }, // Half of height to center
    ],
    opacity: 0.1, // Very transparent (10% opacity)
    zIndex: -1, // Behind all content
  },

  // Header Styles
  header: {
    alignItems: "center",
    paddingTop: 60,
    paddingBottom: 40,
    position: "relative", // Added for absolute positioning of clear button
  },
  logo: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(255, 165, 0, 0.2)",
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
    fontSize: 30,
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

  // Clear Chat Button
  clearButton: {
    position: "absolute",
    top: 20,
    right: 0,
    padding: 12,
    borderRadius: 20,
    backgroundColor: "rgba(255, 0, 0, 0.1)",
    zIndex: 1,
  },
  clearButtonIcon: {
    fontSize: 15,
    color: "#ff4444",
  },

  // Messages
  messagesContainer: {
    flex: 1,
    paddingBottom: 20, // Reduced from 100
  },
  messagesList: {
    flex: 1,
  },
  messageBubble: {
    maxWidth: "85%",
    padding: 14,
    borderRadius: 18,
    marginVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
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
    backgroundColor: "#f0f0f0", // Keep light gray background
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
  aiTimestamp: {
    color: "rgba(0, 0, 0, 0.6)", // Dark timestamp for AI messages (on light background)
  },
  loadingContainer: {
    alignItems: "center",
    padding: 16,
  },
  loadingText: {
    fontStyle: "italic",
  },

  // Suggestions
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
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    opacity: 0.6,
  },
  promptCardDisabled: {
    opacity: 0.3,
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

  // Input - Updated for keyboard handling
  inputContainer: {
    padding: 16,
    paddingTop: 16,
    paddingBottom: 30, // Add safe area bottom padding
    backgroundColor: "transparent",
    borderRadius: 30,
    marginBottom: -45, // Negative margin to extend beyond safe area
  },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 30,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 8, // Reduced from 16 since disclaimer might be hidden
    minHeight: 48,
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
