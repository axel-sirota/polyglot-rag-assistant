import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Vibration,
  Alert,
} from 'react-native';
import { useLocalParticipant, useTracks } from '@livekit/react-native';
import { Track } from 'livekit-client';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Message, FlightResult } from '../types';
import { ChatBubble } from '../components/ChatBubble';
import { FlightCard } from '../components/FlightCard';
import { API_ENDPOINT } from '../config';

export function ChatScreen() {
  const { localParticipant } = useLocalParticipant();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [flightResults, setFlightResults] = useState<FlightResult[]>([]);
  const flatListRef = useRef<FlatList>(null);

  // Subscribe to remote tracks for assistant audio
  const tracks = useTracks([Track.Source.Microphone], {
    onlySubscribed: true,
  });

  useEffect(() => {
    // Add welcome message
    addMessage({
      id: Date.now().toString(),
      text: 'Welcome to Polyglot RAG! Speak or type in any language to search for flights.',
      sender: 'assistant',
      timestamp: new Date(),
    });

    // Set up data receiver
    if (localParticipant) {
      localParticipant.on('dataReceived', handleDataReceived);
    }

    return () => {
      if (localParticipant) {
        localParticipant.off('dataReceived', handleDataReceived);
      }
    };
  }, [localParticipant]);

  const handleDataReceived = (data: Uint8Array) => {
    try {
      const message = JSON.parse(new TextDecoder().decode(data));
      
      switch (message.type) {
        case 'transcription':
          addMessage({
            id: Date.now().toString(),
            text: message.text,
            sender: 'user',
            timestamp: new Date(),
          });
          break;
          
        case 'response':
          addMessage({
            id: Date.now().toString(),
            text: message.text,
            sender: 'assistant',
            timestamp: new Date(),
          });
          if (message.language) {
            setCurrentLanguage(message.language);
          }
          break;
          
        case 'flightResults':
          setFlightResults(message.results);
          break;
      }
    } catch (error) {
      console.error('Data parsing error:', error);
    }
  };

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const sendTextMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputText('');

    try {
      const response = await fetch(`${API_ENDPOINT}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputText,
          language: currentLanguage,
        }),
      });

      const data = await response.json();

      if (data.language) {
        setCurrentLanguage(data.language);
      }

      addMessage({
        id: (Date.now() + 1).toString(),
        text: data.response,
        sender: 'assistant',
        timestamp: new Date(),
      });

      if (data.flightResults) {
        setFlightResults(data.flightResults);
      }
    } catch (error) {
      console.error('Send message error:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
    }
  };

  const startRecording = async () => {
    try {
      setIsRecording(true);
      Vibration.vibrate(50); // Haptic feedback

      const track = await localParticipant.createAudioTrack();
      await localParticipant.publishTrack(track);
    } catch (error) {
      console.error('Recording error:', error);
      setIsRecording(false);
      Alert.alert('Microphone Error', 'Unable to access microphone. Please check permissions.');
    }
  };

  const stopRecording = async () => {
    if (!isRecording) return;

    setIsRecording(false);
    Vibration.vibrate(50); // Haptic feedback

    try {
      localParticipant.unpublishAllTracks();
    } catch (error) {
      console.error('Stop recording error:', error);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <ChatBubble message={item} />
  );

  const getLanguageDisplay = () => {
    const languages: { [key: string]: string } = {
      'en': 'English',
      'es': 'Español',
      'fr': 'Français',
      'de': 'Deutsch',
      'it': 'Italiano',
      'pt': 'Português',
      'ja': '日本語',
      'zh': '中文',
      'ko': '한국어',
      'ar': 'العربية',
      'hi': 'हिन्दी',
      'ru': 'Русский',
    };
    return languages[currentLanguage] || currentLanguage.toUpperCase();
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🌍 Polyglot RAG Assistant</Text>
        <View style={styles.languageBadge}>
          <Text style={styles.languageText}>{getLanguageDisplay()}</Text>
        </View>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messagesList}
        ListFooterComponent={
          flightResults.length > 0 ? (
            <View style={styles.flightResultsContainer}>
              <Text style={styles.flightResultsTitle}>✈️ Flight Results</Text>
              {flightResults.slice(0, 3).map((flight, index) => (
                <FlightCard key={index} flight={flight} />
              ))}
            </View>
          ) : null
        }
      />

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message..."
          placeholderTextColor="#9ca3af"
          multiline
          maxHeight={100}
          onSubmitEditing={sendTextMessage}
        />
        <TouchableOpacity
          style={styles.sendButton}
          onPress={sendTextMessage}
          disabled={!inputText.trim()}
        >
          <Icon 
            name="send" 
            size={24} 
            color={inputText.trim() ? '#ffffff' : '#9ca3af'} 
          />
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.voiceButton, isRecording && styles.voiceButtonRecording]}
        onPressIn={startRecording}
        onPressOut={stopRecording}
        activeOpacity={0.8}
      >
        <Icon name="mic" size={32} color="#ffffff" />
        <Text style={styles.voiceButtonText}>
          {isRecording ? 'Recording...' : 'Hold to Talk'}
        </Text>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  languageBadge: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  languageText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '500',
  },
  messagesList: {
    padding: 16,
    paddingBottom: 100,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButton: {
    position: 'absolute',
    bottom: 100,
    alignSelf: 'center',
    backgroundColor: '#10b981',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 32,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  voiceButtonRecording: {
    backgroundColor: '#ef4444',
  },
  voiceButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  flightResultsContainer: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#ffffff',
    borderRadius: 12,
  },
  flightResultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#1f2937',
  },
});