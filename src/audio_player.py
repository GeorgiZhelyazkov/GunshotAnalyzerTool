import time
import pygame

class AudioPlayer:
    def __init__(self, on_tick_callback, on_stop_callback):
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.paused_time = 0.0
        self.start_play_time = 0.0
        self.on_tick_callback = on_tick_callback
        self.on_stop_callback = on_stop_callback

    def play(self, file_path):
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.start_play_time = time.time() - self.paused_time
                self.is_paused = False
            else:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self.start_play_time = time.time()
            self.is_playing = True
        except Exception as e:
            print(f"Грешка при пускане на аудио: {e}")

    def pause(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.paused_time = time.time() - self.start_play_time

    def stop(self):
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        self.is_playing = self.is_paused = False
        self.paused_time = 0.0
        self.on_stop_callback()

    def set_position(self, file_path, position_seconds):
        if self.is_playing:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=position_seconds)
            self.start_play_time = time.time() - position_seconds
        elif self.is_paused:

            pygame.mixer.music.stop()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=position_seconds)
            pygame.mixer.music.pause()
            self.paused_time = position_seconds
            self.start_play_time = time.time() - position_seconds

    def update_tick(self, max_duration):
        if not self.is_playing:
            return
        current_pos = time.time() - self.start_play_time
        if current_pos <= max_duration:
            self.on_tick_callback(current_pos)
        else:
            self.is_playing = False
            self.stop()