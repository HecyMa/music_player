import os
import json
from io import BytesIO
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.utils import platform
from kivy.clock import Clock
from kivy.graphics import Line, Color
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

EXTENSION = '.mp3'

if platform == 'android':
    DIRECTORY_PATH = '/storage/emulated/0/'
else:
    DIRECTORY_PATH = '.'

music_files = []
playlists = {}

def save_playlists():
    """Сохраняет плейлисты в файл"""
    try:
        with open(os.path.join('.', 'playlists.json'), 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении плейлистов: {e}")

def load_playlists():
    """Загружает плейлисты из файла"""
    global playlists
    try:
        path = os.path.join('.', 'playlists.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                playlists = json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке плейлистов: {e}")
        playlists = {}

def refresh_music_files():
    global music_files
    try:
        music_files = []
        for path, _, files in os.walk(DIRECTORY_PATH):
            if (('Download' in path) or ('Music' in path)) and platform == 'android':
                music_files.extend(
                    [os.path.join(path, file).replace('\\', '/') for file in files if str(file).endswith('.mp3')])
            else:
                music_files.extend(
                    [os.path.join(path, file).replace('\\', '/') for file in files if str(file).endswith('.mp3')])
    except Exception as e:
        print(f'Error: {e}')

load_playlists()
refresh_music_files()

def delete_file(file_path):
    try:
        os.remove(file_path)
        refresh_music_files()
        return True
    except Exception as e:
        print(f'Ошибка удаления файла: {e}')
        return False


def extract_cover_art(mp3_path, output_path=None):
    """Извлекает обложку из MP3 и сохраняет её во временный файл."""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            return None

        for tag in audio.tags.values():
            if tag.FrameID == 'APIC':
                cover_data = tag.data
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(cover_data)

                return cover_data
    except Exception as e:
        print(f"Ошибка при извлечении обложки: {e}")
    return None


class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super(BaseScreen, self).__init__(**kwargs)
        layout = FloatLayout()

        self.sound_on = False
        self.sound = None
        self.previous_name = None
        self.current_position = 0
        self.clock_event = None

        self.background_image = Image(source='wallpaper.jpg', allow_stretch=True, keep_ratio=False)
        layout.add_widget(self.background_image)

        self.content = BoxLayout(orientation='vertical')
        self.content.bind(minimum_height=self.content.setter('height'))

        layout.add_widget(self.content)
        self.add_widget(layout)

    def update_position(self, dt):
        if self.sound and self.sound.state == 'play':
            self.current_position += dt


class InfoWin(BaseScreen):
    def __init__(self, **kwargs):
        super(InfoWin, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        button = Button(text='<', size_hint=(None, None), size=(150, 150), pos_hint={'x': 0.02, 'top': 1}, font_size='30sp')
        button.background_color = (1, 1, 1, 0)
        button.bind(on_press=self.back_to_list)
        layout.add_widget(button)

        label = Label(
            text="Создатель:\nСуханов Дмитрий Сергеевич,\n151320 гр.\nНаписано на библиотеках:\nkivy, mutagen",
            font_size='25sp', pos=(20, 20), size=(180, 100))
        layout.add_widget(label)

        with layout.canvas:
            Color(1, 1, 1, 1)
            Line(points=[0, 2000, 1080, 2000], width=5)

        self.content.add_widget(layout)

    def back_to_list(self, instance):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'list'


class UnitMusicWin(BaseScreen):
    def __init__(self, **kwargs):
        super(UnitMusicWin, self).__init__(**kwargs)
        main_layout = FloatLayout()

        self.current_title = "Unknown Title"
        self.current_artist = "Unknown Artist"
        self.update_event = None
        self.current_playlist = None

        button_back = Button(text='<', size_hint=(None, None), size=(150, 150), pos_hint={'x': 0.02, 'top': 1},
                             font_size='30sp')
        button_back.background_color = (1, 1, 1, 0)
        button_back.bind(on_press=self.back_to_list)
        main_layout.add_widget(button_back)

        button_menu = Button(text=':', size_hint=(None, None), size=(150, 150), pos_hint={'x': 0.85, 'top': 1},
                             font_size='30sp')
        button_menu.background_color = (1, 1, 1, 0)
        button_menu.bind(on_press=self.go_to_menu)
        main_layout.add_widget(button_menu)

        self.label = Label(text=f"{self.current_title}\n{self.current_artist}",
                           pos_hint={'x': 0, 'y': -0.12},
                           font_size='25sp',
                           height=100,
                           width=800,
                           halign='center')
        main_layout.add_widget(self.label)

        self.track_img = Image(
            source='default_pic.jpg',
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            allow_stretch=True,
            keep_ratio=True
        )
        main_layout.add_widget(self.track_img)

        button_prev = Button(text='I<', size_hint=(None, None), size=(150, 150), pos_hint={'x': 0.18, 'y': 0.10},
                             font_size='35sp')
        button_prev.bind(on_press=self.prev_music)
        button_prev.background_color = (1, 1, 1, 0)
        main_layout.add_widget(button_prev)

        self.button_play = Button(text='II', size_hint=(None, None), size=(200, 200), pos_hint={'x': 0.42, 'y': 0.10},
                                  font_size='35sp')
        self.button_play.bind(on_press=self.play_music)
        self.button_play.background_color = (1, 1, 1, 0)
        main_layout.add_widget(self.button_play)

        button_next = Button(text='>I', size_hint=(None, None), size=(150, 150), pos_hint={'x': 0.7, 'y': 0.10},
                             font_size='35sp')
        button_next.background_color = (1, 1, 1, 0)
        button_next.bind(on_press=self.next_music)
        main_layout.add_widget(button_next)

        with main_layout.canvas:
            Color(1, 1, 1, 1)
            Line(points=[0, 2000, 1080, 2000], width=5)

        self.content.add_widget(main_layout)

    def go_to_menu(self, button):
        music_list = self.manager.get_screen('list')
        layout = GridLayout(cols=1, padding=10)
        close_button = Button(text="Назад")
        delete_button = Button(text="Удалить трек")
        layout.add_widget(close_button)
        layout.add_widget(delete_button)

        self.popup = Popup(title='Меню',
                           content=layout,
                           size_hint=(None, None), size=(700, 700))
        self.popup.open()

        close_button.bind(on_press=self.popup.dismiss)
        delete_button.bind(on_press=self.delete_current_track)

    def delete_current_track(self, instance):
        music_list = self.manager.get_screen('list')
        if music_list.previous_name:
            current_index = music_files.index(music_list.previous_name)

            if delete_file(music_list.previous_name):
                music_list.stop_music()

                if len(music_files) > 0:
                    new_index = current_index if current_index < len(music_files) else len(music_files) - 1
                    if new_index >= 0:
                        music_list.play_music(music_files[new_index])
                        self.update_track_info()
                    else:
                        self.current_title = "No tracks"
                        self.current_artist = ""
                        self.label.text = f"{self.current_title}\n{self.current_artist}"
                        self.track_img.source = 'default_pic.jpg'
                        self.track_img.reload()
                else:
                    self.current_title = "No tracks"
                    self.current_artist = ""
                    self.label.text = f"{self.current_title}\n{self.current_artist}"
                    self.track_img.source = 'default_pic.jpg'
                    self.track_img.reload()

                music_list.refresh_list()

                for widget in self.walk():
                    if isinstance(widget, Popup):
                        widget.dismiss()
                        break
        save_playlists()

    def back_to_list(self, instance):
        if self.current_playlist:
            playlist_screen = f'playlist_{self.current_playlist}'
            self.manager.transition = SlideTransition(direction='right')
            self.current_playlist = None
            self.manager.current = playlist_screen
        else:
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'list'

    def prev_music(self, instance):
        if self.current_playlist:
            music_playlist = self.manager.get_screen(f'playlist_{self.current_playlist}')
            print(music_playlist.previous_name)
            music_list = self.manager.get_screen('list')
            if music_playlist.previous_name and len(playlists[self.current_playlist]):
                music_list.stop_music()
                current_index = playlists[self.current_playlist].index(music_playlist.previous_name)
                new_index = current_index - 1 if current_index > 0 else len(playlists[self.current_playlist]) - 1
                music_playlist.previous_name = playlists[self.current_playlist][new_index]
                music_list.play_music(playlists[self.current_playlist][new_index])
                self.update_track_info()
        else:
            music_list = self.manager.get_screen('list')
            if music_list.previous_name and len(music_files) > 0:
                music_list.stop_music()
                current_index = music_files.index(music_list.previous_name)
                new_index = current_index - 1 if current_index > 0 else len(music_files) - 1
                music_list.play_music(music_files[new_index])
                self.update_track_info()

    def play_music(self, instance):
        music_list = self.manager.get_screen('list')
        if music_list.sound_on:
            music_list.pause_music()
            self.button_play.text = '>'
        else:
            music_list.resume_music()
            self.button_play.text = 'II'

    def next_music(self, instance):
        if self.current_playlist:
            music_playlist = self.manager.get_screen(f'playlist_{self.current_playlist}')
            print(music_playlist.previous_name)
            music_list = self.manager.get_screen('list')
            if music_playlist.previous_name and len(playlists[self.current_playlist]) > 0:
                music_list.stop_music()
                current_index = playlists[self.current_playlist].index(music_playlist.previous_name)
                new_index = current_index + 1 if current_index < (len(playlists[self.current_playlist]) - 1) else 0
                music_playlist.previous_name = playlists[self.current_playlist][new_index]
                music_list.play_music(playlists[self.current_playlist][new_index])
                self.update_track_info()
        else:
            music_list = self.manager.get_screen('list')
            if music_list.previous_name and len(music_files) > 0:
                music_list.stop_music()
                current_index = music_files.index(music_list.previous_name)
                new_index = current_index + 1 if current_index < len(music_files) - 1 else 0
                music_list.play_music(music_files[new_index])
                self.update_track_info()

    def on_pre_enter(self, *args):
        self.update_track_info()
        if not self.update_event:
            self.update_event = Clock.schedule_interval(self.update_track_info, 1.5)

    def on_leave(self, *args):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def update_track_info(self, *args):
        if self.manager:
            music_list = self.manager.get_screen('list')
            if music_list.previous_name and len(music_files) > 0:
                try:
                    temp_cover_path = os.path.join('.', 'temp_cover.jpg')
                    cover_data = extract_cover_art(music_list.previous_name, temp_cover_path)

                    if cover_data:
                        with open(temp_cover_path, 'wb') as f:
                            f.write(cover_data)
                        self.track_img.source = temp_cover_path
                    else:
                        self.track_img.source = 'default_pic.jpg'

                    self.track_img.reload()

                    self.button_play.text = 'II' if music_list.sound_on else '>'
                except Exception as e:
                    print(f"Ошибка при обновлении информации: {e}")
                    self.track_img.source = 'default_pic.jpg'
                    self.track_img.reload()
            else:
                self.current_title = "No tracks"
                self.current_artist = ""
                self.label.text = f"{self.current_title}\n{self.current_artist}"
                self.track_img.source = 'default_pic.jpg'
                self.track_img.reload()


class PlaylistScreen(Screen):
    def __init__(self, playlist_name, **kwargs):
        super(PlaylistScreen, self).__init__(**kwargs)
        self.playlist_name = playlist_name
        self.layout = FloatLayout()
        self.previous_name = None

        self.background_image = Image(source='wallpaper.jpg', allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.background_image)

        btn_back = Button(text='<', size_hint=(None, None), size=(150, 150),
                          pos_hint={'x': 0.02, 'top': 1}, font_size='30sp')
        btn_back.background_color = (1, 1, 1, 0)
        btn_back.bind(on_press=self.back_to_playlists)
        self.layout.add_widget(btn_back)

        self.scroll = ScrollView(size_hint=(1, 0.8), pos_hint={'top': 0.9})
        self.track_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.track_list.bind(minimum_height=self.track_list.setter('height'))

        self.refresh_tracks()
        self.scroll.add_widget(self.track_list)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

    def refresh_tracks(self):
        self.track_list.clear_widgets()

        if self.playlist_name in playlists:
            for track_path in playlists[self.playlist_name]:
                try:
                    audio = MP3(track_path, ID3=ID3)
                    title = str(audio.get("TIT2", "Unknown Title"))
                    artist = str(audio.get("TPE1", "Unknown Artist"))

                    btn = Button(text=f'{title} - {artist}', size_hint_y=None, height=150, font_size='20sp')
                    btn.background_color = (1, 1, 1, 0)
                    btn.bind(on_press=lambda x, path=track_path: self.play_track(path))
                    self.track_list.add_widget(btn)
                except:
                    pass

    def play_track(self, track_path):
        self.previous_name = track_path
        unit_screen = self.manager.get_screen('unit')
        unit_screen.current_playlist = self.playlist_name
        self.manager.get_screen('list').play_music(track_path)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'unit'

    def back_to_playlists(self, instance):
        self.manager.transition = SlideTransition(direction='down')
        self.manager.current = 'playlist'


class PlaylistWin(BaseScreen):
    def __init__(self, **kwargs):
        super(PlaylistWin, self).__init__(**kwargs)
        self.main_layout = FloatLayout()

        button_back = Button(text='<', size_hint=(None, None), size=(150, 150),
                             pos_hint={'x': 0.02, 'top': 1}, font_size='30sp')
        button_back.background_color = (1, 1, 1, 0)
        button_back.bind(on_press=self.back_to_list)
        self.main_layout.add_widget(button_back)

        btn_add = Button(text='+', size_hint=(None, None), size=(150, 150),
                         pos_hint={'x': 0.85, 'top': 1}, font_size='30sp')
        btn_add.background_color = (1, 1, 1, 0)
        btn_add.bind(on_press=self.show_add_playlist_dialog)
        self.main_layout.add_widget(btn_add)

        self.scroll = ScrollView(size_hint=(1, 0.8), pos_hint={'top': 0.9})
        self.playlist_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.playlist_list.bind(minimum_height=self.playlist_list.setter('height'))

        self.refresh_playlists()
        self.scroll.add_widget(self.playlist_list)
        self.main_layout.add_widget(self.scroll)

        with self.main_layout.canvas:
            Color(1, 1, 1, 1)
            Line(points=[0, 2000, 1080, 2000], width=5)

        self.content.add_widget(self.main_layout)

    def refresh_playlists(self):
        self.playlist_list.clear_widgets()

        for name in playlists:
            hbox = BoxLayout(size_hint_y=None, height=150)

            btn = Button(text=name, font_size='20sp')
            btn.background_color = (1, 1, 1, 0)
            btn.bind(on_press=lambda x, n=name: self.open_playlist(n))
            hbox.add_widget(btn)

            btn_del = Button(text='×', size_hint_x=None, width=150, font_size='20sp')
            btn_del.background_color = (1, 1, 1, 0)
            btn_del.bind(on_press=lambda x, n=name: self.delete_playlist(n))
            hbox.add_widget(btn_del)

            self.playlist_list.add_widget(hbox)

    def delete_playlist(self, playlist_name):
        content = BoxLayout(orientation='vertical', spacing=10)
        label = Label(text=f"Удалить плейлист '{playlist_name}'?")
        content.add_widget(label)

        btn_box = BoxLayout(size_hint_y=None, height=50)
        btn_cancel = Button(text='Отмена')
        btn_delete = Button(text='Удалить')
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_delete)
        content.add_widget(btn_box)

        popup = Popup(title='Удаление плейлиста',
                      content=content,
                      size_hint=(0.7, 0.4))

        def do_delete(instance):
            if playlist_name in playlists:
                del playlists[playlist_name]
                save_playlists()
                self.refresh_playlists()
            popup.dismiss()

        btn_cancel.bind(on_press=popup.dismiss)
        btn_delete.bind(on_press=do_delete)
        popup.open()

    def open_playlist(self, name):
        if name not in self.manager.screen_names:
            self.manager.add_widget(PlaylistScreen(playlist_name=name, name=f'playlist_{name}'))
        self.manager.transition = SlideTransition(direction='up')
        self.manager.current = f'playlist_{name}'

    def show_add_playlist_dialog(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10)

        input_name = TextInput(hint_text='Название плейлиста', size_hint_y=None, height=150)
        content.add_widget(input_name)

        btn_box = BoxLayout(size_hint_y=None, height=100)
        btn_cancel = Button(text='Отмена')
        btn_create = Button(text='Создать')
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_create)
        content.add_widget(btn_box)

        popup = Popup(title='Новый плейлист', content=content,
                      size_hint=(0.8, 0.4))

        def create_playlist(inst):
            name = input_name.text.strip()
            if name and name not in playlists:
                playlists[name] = []
                save_playlists()
                self.refresh_playlists()
                self.show_add_tracks_dialog(name)
            popup.dismiss()

        btn_cancel.bind(on_press=popup.dismiss)
        btn_create.bind(on_press=create_playlist)
        popup.open()

    def show_add_tracks_dialog(self, playlist_name):
        content = BoxLayout(orientation='vertical', spacing=10)

        scroll = ScrollView()
        track_list = BoxLayout(orientation='vertical', size_hint_y=None)
        track_list.bind(minimum_height=track_list.setter('height'))

        selected_tracks = []

        for track_path in music_files:
            try:
                audio = MP3(track_path, ID3=ID3)
                title = str(audio.get("TIT2", "Unknown Title"))
                artist = str(audio.get("TPE1", "Unknown Artist"))

                hbox = BoxLayout(size_hint_y=None, height=150)
                cb = CheckBox(size_hint_x=None, width=150)
                lbl = Label(text=f'{title} - {artist}')
                print(f'{title} - {artist}')
                hbox.add_widget(lbl)
                hbox.add_widget(cb)
                track_list.add_widget(hbox)

                def on_checkbox_active(checkbox, active, path=track_path):
                    if active:
                        selected_tracks.append(path)
                    elif path in selected_tracks:
                        selected_tracks.remove(path)

                cb.bind(active=on_checkbox_active)
            except Exception as e:
                print(f'Не удалось найти треки: {e}')

        scroll.add_widget(track_list)
        content.add_widget(scroll)

        btn_box = BoxLayout(size_hint_y=None, height=50)
        btn_cancel = Button(text='Отмена')
        btn_save = Button(text='Сохранить')
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_save)
        content.add_widget(btn_box)

        popup = Popup(title=f'Добавить треки в "{playlist_name}"',
                      content=content, size_hint=(0.9, 0.8))

        def save_tracks(inst):
            playlists[playlist_name].extend(selected_tracks)
            save_playlists()
            popup.dismiss()
            self.refresh_playlists()

        btn_cancel.bind(on_press=popup.dismiss)
        btn_save.bind(on_press=save_tracks)
        popup.open()

    def back_to_list(self, instance):
        self.manager.transition = SlideTransition(direction='down')
        self.manager.current = 'list'


class MusicList(BaseScreen):
    def __init__(self, **kwargs):
        super(MusicList, self).__init__(**kwargs)
        self.main_layout = FloatLayout()

        self.label = Label(text=f"Песен: {len(music_files)}",
                           pos_hint={'x': -0.33, 'y': 0.225},
                           font_size='25sp')

        settings_button = Button(text='?', size_hint=(None, None), size=(150, 150),
                                 pos_hint={'x': 0.02, 'top': 1}, font_size='30sp')
        settings_button.background_color = (1, 1, 1, 0)
        settings_button.bind(on_press=self.go_to_info)

        music_button = Button(text='Песня', size_hint=(None, None), size=(450, 100),
                              pos_hint={'x': 0.05, 'y': 0.80}, font_size='30sp')
        music_button.background_color = (1, 1, 1, 0)
        music_button.bind(on_press=self.go_to_unit)

        playlist_button = Button(text='Плейлист', size_hint=(None, None), size=(450, 100),
                                 pos_hint={'x': 0.54, 'y': 0.80}, font_size='30sp')
        playlist_button.background_color = (1, 1, 1, 0)
        playlist_button.bind(on_press=self.go_to_playlist)

        self.layout_music = BoxLayout(orientation='vertical', size_hint_y=None)
        self.layout_music.bind(minimum_height=self.layout_music.setter('height'))
        self.scroll_view = ScrollView(size_hint=(1, 0.7), size=(400, 300))

        self.main_layout.add_widget(settings_button)
        self.main_layout.add_widget(self.label)
        self.main_layout.add_widget(music_button)
        self.main_layout.add_widget(playlist_button)
        self.main_layout.add_widget(self.scroll_view)

        with self.main_layout.canvas:
            Color(1, 1, 1, 1)
            Line(points=[0, 2000, 1080, 2000], width=5)
            Line(points=[0, 1730, 1080, 1730], width=5)
            Line(points=[540, 1730, 540, 1850], width=5)
            Line(points=[0, 1530, 1080, 1530], width=5)

        self.content.add_widget(self.main_layout)

        self.refresh_list()

    def refresh_list(self):
        """Обновляет список песен в ScrollView"""
        self.layout_music.clear_widgets()

        for sound_name in music_files:
            try:
                audio = MP3(sound_name, ID3=ID3)
                title = str(audio.get("TIT2", "Unknown Title"))
                artist = str(audio.get("TPE1", "Unknown Artist"))

                play_button = Button(text=f'{title} - {artist}',
                                     size_hint=(1, None),
                                     height=150,
                                     font_size='20sp',
                                     halign='left')
                play_button.background_color = (1, 1, 1, 0)
                play_button.bind(on_press=lambda instance, file=sound_name: self.play_music(file))
                self.layout_music.add_widget(play_button)
            except Exception as e:
                print('Error:', e, 'Error file:', sound_name)

        self.scroll_view.clear_widgets()
        self.scroll_view.add_widget(self.layout_music)
        self.label.text = f"Песен: {len(music_files)}"

    def go_to_info(self, instance):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'info'

    def go_to_playlist(self, instance):
        self.manager.transition = SlideTransition(direction='up')
        self.manager.current = 'playlist'

    def go_to_unit(self, instance):
        if self.previous_name:
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'unit'

    def stop_music(self):
        if self.sound:
            if self.clock_event:
                self.clock_event.cancel()
            self.sound.stop()
            self.sound_on = False
            self.current_position = 0

    def pause_music(self):
        if self.sound and self.sound_on:
            if self.clock_event:
                self.clock_event.cancel()
            self.sound.stop()
            self.sound_on = False

    def resume_music(self):
        if self.sound and not self.sound_on:
            self.sound.play()
            self.sound_on = True
            self.clock_event = Clock.schedule_interval(self.update_position, 0.1)
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'unit'

    def play_music(self, name):
        try:
            if self.previous_name != name:
                self.stop_music()
                self.sound = SoundLoader.load(name)
                if self.sound:
                    self.sound.play()
                    self.sound_on = True
                    self.previous_name = name
                    self.clock_event = Clock.schedule_interval(self.update_position, 0.1)
                    self.manager.transition = SlideTransition(direction='left')
                    self.manager.current = 'unit'
            else:
                if self.sound_on:
                    self.pause_music()
                else:
                    self.resume_music()

        except Exception as e:
            print(f'Error: {e}')


class MusicApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MusicList(name="list"))
        sm.add_widget(InfoWin(name="info"))
        sm.add_widget(UnitMusicWin(name="unit"))
        sm.add_widget(PlaylistWin(name="playlist"))
        return sm


if __name__ == '__main__':
    try:
        MusicApp().run()
    except Exception as e:
        print(f'App error: {e}')
