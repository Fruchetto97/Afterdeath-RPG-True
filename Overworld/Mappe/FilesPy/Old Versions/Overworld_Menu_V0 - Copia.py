# Overworld_Menu_V0.py
# Contains PauseMenu and all menu-related logic for the overworld
import pygame

class PauseMenu:
    def __init__(self, screen_width, screen_height, player_stats):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.player_stats = player_stats
        self.player_img_path = player_stats.gif_path
        self.frame_png = None
        self.frame_png_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Overworld\Menus\Pause_Menu_V01.png"
        self.frame_png_orig = None
        self.frame_png_size = (0, 0)
        self._set_menu_box()
        self.player_frames = []
        self.player_frame_durations = []
        self.player_frame_index = 0
        self.player_frame_timer = 0
        self.player_frame_count = 1
        self.player_img = None
        self._update_gif_scale()

    def _update_gif_scale(self):
        try:
            from PIL import Image
            pil_img = Image.open(self.player_img_path)
            self.player_frames = []
            self.player_frame_durations = []
            gif_scale = 0.85
            gif_target_height = int(self.menu_box_height * gif_scale)
            aspect = pil_img.width / pil_img.height if pil_img.height != 0 else 1
            gif_target_width = int(gif_target_height * aspect)
            for frame in range(0, getattr(pil_img, 'n_frames', 1)):
                pil_img.seek(frame)
                frame_img = pil_img.convert('RGBA')
                mode = frame_img.mode
                size = frame_img.size
                data = frame_img.tobytes()
                surf = pygame.image.fromstring(data, size, mode)
                surf = pygame.transform.smoothscale(surf, (gif_target_width, gif_target_height))
                self.player_frames.append(surf)
                duration = pil_img.info.get('duration', 100)
                self.player_frame_durations.append(duration)
            self.player_frame_count = len(self.player_frames)
            self.player_img = self.player_frames[0] if self.player_frames else None
            self.gif_target_width = gif_target_width
            self.gif_target_height = gif_target_height
        except ImportError:
            print("[PauseMenu] Pillow (PIL) not installed. GIF loading may fail.")
            try:
                img = pygame.image.load(self.player_img_path).convert_alpha()
                aspect = img.get_width() / img.get_height() if img.get_height() != 0 else 1
                gif_scale = 0.7
                gif_target_height = int(self.menu_box_height * gif_scale)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e:
                print(f"[PauseMenu] Could not load player image: {e}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.7)
        except Exception as e:
            print(f"[PauseMenu] Could not load GIF with Pillow: {e}")
            try:
                img = pygame.image.load(self.player_img_path).convert_alpha()
                aspect = img.get_width() / img.get_height() if img.get_height() != 0 else 1
                gif_scale = 0.7
                gif_target_height = int(self.menu_box_height * gif_scale)
                gif_target_width = int(gif_target_height * aspect)
                self.player_img = pygame.transform.smoothscale(img, (gif_target_width, gif_target_height))
                self.gif_target_width = gif_target_width
                self.gif_target_height = gif_target_height
            except Exception as e2:
                print(f"[PauseMenu] Could not load player image: {e2}")
                self.player_img = None
                self.gif_target_width = 120
                self.gif_target_height = int(self.menu_box_height * 0.7)
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            self.font = pygame.font.Font(font_path, 32)
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.Font(font_path, font_big_size)
        except Exception as e:
            print(f"[PauseMenu] Could not load Pixellari.ttf: {e}")
            self.font = pygame.font.SysFont(None, 32, bold=True)
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.SysFont(None, font_big_size, bold=True)

    def _set_menu_box(self):
        # Always keep width at 85% of screen width, height/width ratio 1:2
        menu_box_width = int(self.screen_width * 0.85)
        menu_box_height = int(menu_box_width / 2.0545454)
        # If height exceeds screen, adjust width and height
        if menu_box_height > self.screen_height:
            menu_box_height = self.screen_height
            menu_box_width = int(menu_box_height * 2)
        self.menu_box_width = menu_box_width
        self.menu_box_height = menu_box_height
        self.menu_box_x = (self.screen_width - self.menu_box_width) // 2
        self.menu_box_y = (self.screen_height - self.menu_box_height) // 2
        self.menu_surface = pygame.Surface((self.menu_box_width, self.menu_box_height), pygame.SRCALPHA)
        self.menu_surface.fill((30, 30, 40, 200))
        self._update_gif_scale()

    def reload_frame_png(self):
        try:
            self.frame_png_orig = pygame.image.load(self.frame_png_path).convert_alpha()
        except Exception as e:
            print(f"Could not load PNG frame: {e}")
            self.frame_png_orig = None
        self.update_frame_png()

    def update(self, dt):
        if self.player_frame_count > 1 and self.player_frames:
            self.player_frame_timer += dt
            frame_duration = self.player_frame_durations[self.player_frame_index]
            if self.player_frame_timer >= frame_duration:
                self.player_frame_timer = 0
                self.player_frame_index = (self.player_frame_index + 1) % self.player_frame_count
                self.player_img = self.player_frames[self.player_frame_index]

    def update_frame_png(self):
        if self.frame_png_orig:
            scale_factor = 1
            orig_w, orig_h = self.frame_png_orig.get_width(), self.frame_png_orig.get_height()
            scale_h = int(self.menu_box_height * scale_factor)
            scale_w = int(scale_h * (orig_w / orig_h))
            self.frame_png = pygame.transform.smoothscale(self.frame_png_orig, (scale_w, scale_h))
            self.frame_png_size = (scale_w, scale_h)
        else:
            self.frame_png = None
            self.frame_png_size = (0, 0)

    def draw(self, screen):
        self.menu_surface.fill((30, 30, 40, 200))
        self.update_frame_png()
        frame_w, frame_h = 0, 0
        frame_x, frame_y = 0, 0
        if self.frame_png:
            frame_w, frame_h = self.frame_png_size
            frame_x = 0
            frame_y = self.menu_box_height - frame_h
        # Move GIF by 1/4 of the menu PNG width to the left
        shift_left = int(frame_w // 3.65)
        if self.player_img and self.frame_png:
            gif_x = frame_x + (frame_w - self.gif_target_width) // 2 + 20 - shift_left
            gif_y = frame_y + (frame_h - self.gif_target_height) // 2 + 25
            self.menu_surface.blit(self.player_img, (gif_x, gif_y))
        elif self.player_img:
            gif_x = (self.menu_box_width - self.gif_target_width) // 2 + 20 - shift_left
            gif_y = (self.menu_box_height - self.gif_target_height) // 2 + 25
            self.menu_surface.blit(self.player_img, (gif_x, gif_y))
        if self.frame_png:
            self.menu_surface.blit(self.frame_png, (frame_x, frame_y))
        stats_x = (frame_x + frame_w) + 22 if self.frame_png else 30 + self.gif_target_width + 22
        bars_y = (frame_y + (frame_h - self.gif_target_height) // 2) + 100 if self.frame_png else ((self.menu_box_height - self.gif_target_height) // 2) + 100
        bar_width = int(self.menu_box_width * 0.16)
        bar_height = int(32 * 0.90)
        bar_gap = 32
        hp_ratio = self.player_stats.hp / self.player_stats.max_hp if self.player_stats.max_hp > 0 else 0
        hp_bar_rect = pygame.Rect(stats_x, bars_y, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 20, 20), hp_bar_rect)
        pygame.draw.rect(self.menu_surface, (200, 0, 0), (stats_x, bars_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), hp_bar_rect, 2)
        hp_text = f"HEALTH: {int(self.player_stats.hp)} / {int(self.player_stats.max_hp)}"
        hp_surface = self.font.render(hp_text.upper(), True, (255,255,255))
        hp_text_x = stats_x + bar_width + 18
        hp_text_y = bars_y + (bar_height - hp_surface.get_height()) // 2
        self.menu_surface.blit(hp_surface, (hp_text_x, hp_text_y))
        stamina_ratio = self.player_stats.stamina / self.player_stats.max_stamina if self.player_stats.max_stamina > 0 else 0
        stamina_bar_rect = pygame.Rect(stats_x, bars_y + bar_height + bar_gap, bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 60, 20), stamina_bar_rect)
        pygame.draw.rect(self.menu_surface, (0, 200, 0), (stats_x, bars_y + bar_height + bar_gap, int(bar_width * stamina_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), stamina_bar_rect, 2)
        stamina_text = f"STAMINA: {int(self.player_stats.stamina)} / {int(self.player_stats.max_stamina)}"
        stamina_surface = self.font.render(stamina_text.upper(), True, (255,255,255))
        stamina_text_x = stats_x + bar_width + 18
        stamina_text_y = bars_y + bar_height + bar_gap + (bar_height - stamina_surface.get_height()) // 2
        self.menu_surface.blit(stamina_surface, (stamina_text_x, stamina_text_y))
        regen_ratio = self.player_stats.regen / self.player_stats.max_regen if self.player_stats.max_regen > 0 else 0
        regen_bar_rect = pygame.Rect(stats_x, bars_y + 2*(bar_height + bar_gap), bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (20, 20, 60), regen_bar_rect)
        pygame.draw.rect(self.menu_surface, (0, 120, 255), (stats_x, bars_y + 2*(bar_height + bar_gap), int(bar_width * regen_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), regen_bar_rect, 2)
        regen_text = f"REGEN: {int(self.player_stats.regen)} / {int(self.player_stats.max_regen)}"
        regen_surface = self.font.render(regen_text.upper(), True, (255,255,255))
        regen_text_x = stats_x + bar_width + 18
        regen_text_y = bars_y + 2*(bar_height + bar_gap) + (bar_height - regen_surface.get_height()) // 2
        self.menu_surface.blit(regen_surface, (regen_text_x, regen_text_y))
        reserve_ratio = self.player_stats.reserve / self.player_stats.max_reserve if self.player_stats.max_reserve > 0 else 0
        reserve_bar_rect = pygame.Rect(stats_x, bars_y + 3*(bar_height + bar_gap), bar_width, bar_height)
        pygame.draw.rect(self.menu_surface, (60, 60, 20), reserve_bar_rect)
        pygame.draw.rect(self.menu_surface, (255, 200, 0), (stats_x, bars_y + 3*(bar_height + bar_gap), int(bar_width * reserve_ratio), bar_height))
        pygame.draw.rect(self.menu_surface, (255,255,255), reserve_bar_rect, 2)
        reserve_text = f"RESERVE: {int(self.player_stats.reserve)} / {int(self.player_stats.max_reserve)}"
        reserve_surface = self.font.render(reserve_text.upper(), True, (255,255,255))
        reserve_text_x = stats_x + bar_width + 18
        reserve_text_y = bars_y + 3*(bar_height + bar_gap) + (bar_height - reserve_surface.get_height()) // 2
        self.menu_surface.blit(reserve_surface, (reserve_text_x, reserve_text_y))
        screen.blit(self.menu_surface, (self.menu_box_x, self.menu_box_y))
        if self.frame_png:
            name_text = self.player_stats.name or "NO NAME"
            name_surface = self.font_big.render(name_text, True, (255,255,255))
            rect_width = name_surface.get_width() + 40
            rect_height = name_surface.get_height() + 18
            # Move name by 1/4 of the menu PNG width to the left
            rect_x = self.menu_box_x + frame_x + (frame_w - rect_width) // 2 - shift_left
            rect_y = self.menu_box_y + frame_y + (frame_h - rect_height) // 2
            rect_x += 0
            rect_y -= frame_h // 2.23
            text_x = rect_x + (rect_width - name_surface.get_width()) // 2
            text_y = rect_y + (rect_height - name_surface.get_height()) // 2
            screen.blit(name_surface, (text_x, text_y))

    def update_dimensions(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self._set_menu_box()
        try:
            font_path = r"C:\Users\franc\Desktop\Afterdeath_RPG\Fonts\Pixellari.ttf"
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.Font(font_path, font_big_size)
        except Exception as e:
            print(f"[PauseMenu] Could not load Pixellari.ttf for resize: {e}")
            font_big_size = max(26, min(70, int(self.screen_height * 0.050)))
            self.font_big = pygame.font.SysFont(None, font_big_size, bold=True)
        self._update_gif_scale()
        self.update_frame_png()

# --- Menu system entry point ---
def show_pause_menu(screen, pause_menu, dt):
    pause_menu.update(dt)
    pause_menu.draw(screen)
