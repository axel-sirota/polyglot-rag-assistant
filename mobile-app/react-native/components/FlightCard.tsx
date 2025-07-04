import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { FlightResult } from '../types';

interface FlightCardProps {
  flight: FlightResult;
}

export function FlightCard({ flight }: FlightCardProps) {
  const formatTime = (isoTime: string) => {
    try {
      const date = new Date(isoTime);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoTime;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.airline}>{flight.airline}</Text>
        <Text style={styles.flightNumber}>{flight.flight_number}</Text>
      </View>
      
      <View style={styles.details}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>🛫 Departure</Text>
          <Text style={styles.detailValue}>{formatTime(flight.departure_time)}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>🛬 Arrival</Text>
          <Text style={styles.detailValue}>{formatTime(flight.arrival_time)}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>⏱️ Duration</Text>
          <Text style={styles.detailValue}>{flight.duration}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>🔄 Stops</Text>
          <Text style={styles.detailValue}>{flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}</Text>
        </View>
      </View>
      
      <View style={styles.priceContainer}>
        <Text style={styles.price}>{flight.price}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  airline: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  flightNumber: {
    fontSize: 14,
    color: '#6b7280',
  },
  details: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  detailValue: {
    fontSize: 14,
    color: '#1f2937',
    fontWeight: '500',
  },
  priceContainer: {
    alignItems: 'flex-end',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10b981',
  },
});