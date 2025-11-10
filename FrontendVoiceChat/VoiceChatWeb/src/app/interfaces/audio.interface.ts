export interface AudioInterface {
  id: string;
  content: string;  // URL del audio
  sender: 'user' | 'bot';
  timestamp: Date;
}