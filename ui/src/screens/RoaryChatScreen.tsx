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
} from "react-native";

const { width } = Dimensions.get("window");

// Sample suggested prompts - we'll make these dynamic later
const SUGGESTED_PROMPTS = [
  {
    id: 1,
    title: "Important Dates",
    subtitle: "When does fall start?",
  },
  {
    id: 2,
    title: "Prospective Students",
    subtitle: "What is the application deadline?",
  },
  {
    id: 3,
    title: "Alumni",
    subtitle: "How do I get in touch with my old classmates?",
  },
  {
    id: 4,
    title: "Security Tips",
    subtitle: "How can I browse safely?",
  },
];

export const RoaryChatScreen: React.FC = () => {
  const [inputText, setInputText] = useState("");
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

  const handlePromptPress = (prompt: (typeof SUGGESTED_PROMPTS)[0]) => {
    setInputText(prompt.title + " " + prompt.subtitle);
  };

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    // TODO: Integrate with OpenWebUI service
    console.log("Sending:", inputText);
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
        </View>

        {/* Suggested Prompts Section */}
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
                <Text style={[styles.promptSubtitle, themeStyles.subtitleText]}>
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
              style={styles.iconButton}
              onPress={handleSendMessage}
            >
              <Text style={[styles.icon, themeStyles.subtitleText]}>↑</Text>
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
  icon: {
    fontSize: 16,
  },
  disclaimer: {
    fontSize: 12,
    textAlign: "center",
    marginTop: 4,
  },
});
