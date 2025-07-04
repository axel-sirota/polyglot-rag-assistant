import React, { useEffect, useState } from 'react';
import { 
  SafeAreaView, 
  StatusBar, 
  StyleSheet, 
  View, 
  Text,
  ActivityIndicator 
} from 'react-native';
import { LiveKitRoom, useRoom, AudioSession } from '@livekit/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatScreen } from './screens/ChatScreen';
import { API_ENDPOINT, LIVEKIT_URL } from './config';

export default function App() {
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Get or create user ID
      let userId = await AsyncStorage.getItem('userId');
      if (!userId) {
        userId = `mobile-user-${Date.now()}`;
        await AsyncStorage.setItem('userId', userId);
      }

      // Get LiveKit token
      const response = await fetch(`${API_ENDPOINT}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identity: userId,
          room: 'polyglot-rag-demo',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get access token');
      }

      const data = await response.json();
      setToken(data.token);
    } catch (err) {
      console.error('Initialization error:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
        <Text style={styles.loadingText}>Connecting to Polyglot RAG...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (!token) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>No access token available</Text>
      </View>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={LIVEKIT_URL}
      token={token}
      audio={true}
      video={false}
      connect={true}
      options={{
        adaptiveStream: true,
        dynacast: true,
      }}
    >
      <AudioSession />
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
        <ChatScreen />
      </SafeAreaView>
    </LiveKitRoom>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6b7280',
  },
  errorText: {
    fontSize: 16,
    color: '#ef4444',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
});