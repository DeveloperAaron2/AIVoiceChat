import { Component, EventEmitter, forwardRef, Input, OnDestroy, Output, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-audio-recorder',
  templateUrl: './audio-recorder.component.html',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => AudioRecorderComponent),
      multi: true,
    },
  ],
  standalone: true,
})
export class AudioRecorderComponent implements ControlValueAccessor, OnDestroy {
  @Input() mimeType: string = 'audio/webm';          // ajusta a 'audio/webm;codecs=opus' o 'audio/mp4' según el navegador
  @Input() timeslice?: number;                       // opcional: en ms para ondataavailable
  @Output() recorded = new EventEmitter<Blob>();     // opcional: evento por si también lo quieres “emitir”

  public isRecording = signal<boolean>(false);
  public audioUrl = signal<string|null>(null);
 
  private mediaRecorder?: MediaRecorder;
  private chunks: BlobPart[] = [];
  private stream?: MediaStream;

  // ControlValueAccessor
  private onChange: (value: Blob | null) => void = () => {};
  private onTouched: () => void = () => {};
  private isDisabled = false;

  async toggleRecording() {
    if (this.isDisabled) return;
    if (!this.isRecording()) {
      this.isRecording.set(true);
      await this.startRecording();
    } else {
      this.stopRecording();
    }
  }

  async startRecording() {
    try {
      this.onTouched();
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: this.mimeType as MediaRecorderOptions['mimeType'] });
      this.chunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.chunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this.isRecording.set(false);
        const blob = new Blob(this.chunks, { type: this.mimeType });
        // Actualiza preview
        if (this.audioUrl()) URL.revokeObjectURL(this.audioUrl()!);
        this.audioUrl.set(URL.createObjectURL(blob));

        // Entrega valor al FormControl
        this.onChange(blob);
        // Emite por evento, si te interesa escuchar fuera
        this.recorded.emit(blob);

        // Limpia tracks
        this.cleanupStream();
      };

      this.mediaRecorder.start(this.timeslice); // si no hay timeslice, graba continuo
      

      // Al comenzar a grabar, limpia valor anterior del control
      this.onChange(null);
      if (this.audioUrl) {
        URL.revokeObjectURL(this.audioUrl()!);
        this.audioUrl.set(null);
      }
    } catch (err) {
      console.error('Error al acceder al micrófono:', err);
      alert('No se pudo acceder al micrófono.');
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.isRecording.set(false);
  }

  // ControlValueAccessor impl
  writeValue(value: Blob | null): void {
    // Si el formulario escribe un valor (p.ej. reset), reflejarlo en el preview
    if (!value) {
      if (this.audioUrl()) URL.revokeObjectURL(this.audioUrl()!);
      this.audioUrl.set(null);
      return;
    }
    if (this.audioUrl()) URL.revokeObjectURL(this.audioUrl()!);
    this.audioUrl.set(URL.createObjectURL(value));
  }

  registerOnChange(fn: (value: Blob | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.isDisabled = isDisabled;
  }

  ngOnDestroy(): void {
    try {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop();
      }
    } finally {
      this.cleanupStream();
      if (this.audioUrl()) URL.revokeObjectURL(this.audioUrl()!);
    }
  }

  private cleanupStream() {
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = undefined;
  }
}
