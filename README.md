# Музыкальный плеер для андроид смартфонов
## Автор: HecyMa

Простой и функциональный музыкальный плеер для Android, созданный на Python с использованием фреймворка Kivy и сборщика Buildozer.
### 🚀 О проекте
Этот проект представляет собой кроссплатформенное приложение-музыкальный плеер, разработанное для операционной системы Android. Приложение позволяет воспроизводить аудиофайлы с устройства, управлять воспроизведением и просматривать обложки треков.

### 🛠 Технологии
* Python - основной язык программирования
* Kivy - фреймворк для создания кроссплатформенных приложений
* Buildozer - инструмент для сборки Android-приложений из Python-кода
* KivyMD (опционально) - для Material Design интерфейса

### 🔧 Сборка приложения
#### Предварительные требования
1. Установите зависимости для Buildozer (на Linux):
```
sudo apt update
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-devsudo apt update
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```
2. Установите Buildozer:
```
pip3 install --user --upgrade buildozer
```
3. Настройте переменные окружения (добавьте в ~/.bashrc):
```
export PATH=$PATH:~/.local/bin/
```

#### Процесс сборки
1. Клонируйте репозиторий:
```
git clone https://github.com/HecyMa/music_player.git
cd music_player
```
2. Инициализируйте Buildozer (если нужно):
```
buildozer init
```
3. Настройте buildozer.spec (если нужно). Отредактируйте файл buildozer.spec, убедитесь что указаны:
* Название пакета (package.name)
* Иконка приложения (icon.filename)
* Требуемые разрешения (android.permissions)
* Зависимости (requirements)
4. Выполните сборку:
```
buildozer -v android debug
```
