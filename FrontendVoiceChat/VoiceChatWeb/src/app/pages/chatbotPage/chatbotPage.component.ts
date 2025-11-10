import { ChangeDetectionStrategy, Component, inject, signal, ViewChild } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AudioInterface } from '../../interfaces/audio.interface';
import { v4 as uuidv4 } from 'uuid'; // npm install uuid
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';

import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { map, Observable, of } from 'rxjs';
import { DatePipe } from '@angular/common';
import { AudioRecorderComponent } from "../../components/audio-recorder/audio-recorder.component";

@Component({
  selector: 'app-chatbot-page',
  imports: [ReactiveFormsModule, DatePipe, AudioRecorderComponent],
  templateUrl: './chatbotPage.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatbotPageComponent {


  ngOnInit() {
    this.scrollToBottom();
  }

  chatAudios = signal<AudioInterface[]>([
  ]);

  @ViewChild('childRef') child!: AudioRecorderComponent;
  isSending = signal(false);

  fb = inject(FormBuilder);
  private baseUrl = environment.flaskUrl;
  private http = inject(HttpClient);

  myForm = this.fb.group({
    audio: [null, Validators.required],
  });


  private scrollToBottom(): void {
    const chatWindow = document.getElementById('chat-window');
    if (chatWindow) {
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  }



   public uploadAudio(audioBlob: Blob): void {
    this.isSending.set(true);
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');
    // No pongas headers Content-Type cuando mandas FormData
    this.http.post(
      `${this.baseUrl}stt`,
      formData,
      { responseType: 'blob' }  // 👈 clave: esperamos binario, no JSON
    ).subscribe({
      next: (blob: Blob) => {
        const audioUrl = URL.createObjectURL(blob);
        this.chatAudios.update(audios => [...audios, {
          id: uuidv4(),
          content: audioUrl,
          sender: 'bot',
          timestamp: new Date(),
        }]);
        this.isSending.set(false);
        this.child.audioUrl.set(null); // Resetea el reproductor
        this.child.isRecording.set(false);
        this.scrollToBottom();
        
      },
      error: (err) => {
        console.error('Error recibiendo audio:', err);
      }
    });
  }
  public onSubmit(): void {
    if (this.myForm.invalid) return;

    const audioBlob = this.myForm.value.audio; // <-- aquí tienes el Blob
    console.log('Blob de audio:', audioBlob);
    // Ejemplo: enviarlo a backend
    this.uploadAudio(audioBlob!);
  }
  }
 

  //   // Lógica para enviar el mensaje al chatbot y manejar la respuesta
  //   if (!message.trim()) return;

  //   const newMessage: Message = {
  //     id: uuidv4(),
  //     content: message,
  //     sender: 'user',
  //     timestamp: new Date(),
  //   };

  //   this.chatMessages.update(messages => [...messages, newMessage]);
  //   this.myForm.reset();
  //   this.scrollToBottom();
  //   console.log('Mensaje enviado:', message);
  //   this.http.post<{ result: string }>(`${this.baseUrl}generate`, { prompt: message }, {
  //     headers: { 'Content-Type': 'application/json' }
  //     }).pipe(
  //         map(response => response.result),
  //     ).subscribe((messageBot) => {
  //       if(messageBot){
  //         const botMessage: Message = {
  //           id: uuidv4(),
  //           content: messageBot,
  //           sender: 'bot',
  //           timestamp: new Date(),
  //         };
  //         this.chatMessages.update(messages => [...messages, botMessage]);
  //         console.log('respuesta del bot:', messageBot); // ✅ ahora muestra el texto real
  //         this.scrollToBottom();
  //       }
        
  //     });
    
    // Aquí puedes agregar la lógica para interactuar con el backend o servicio del chatbot

  
