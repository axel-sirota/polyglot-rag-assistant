export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant' | 'system';
  timestamp: Date;
}

export interface FlightResult {
  airline: string;
  flight_number: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  price: string;
  stops: number;
  aircraft?: string;
  booking_link?: string;
}