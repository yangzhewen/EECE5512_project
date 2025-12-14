# Glass Test Android App

Android application that integrates the YouTube video quality logger.

## Features

- **WebView Integration**: Embeds test.html in a native Android app
- **JavaScript Bridge**: Allows saving logs to device storage
- **Download Logs**: Native button to trigger log download
- **Clear Logs**: Reset the log data
- **Auto-save**: Logs are saved to app-specific storage
- **Full YouTube API Support**: Enables video playback and quality monitoring

## Project Structure

```
android_app/
├── app/
│   ├── build.gradle
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/com/glasstest/
│           │   └── MainActivity.java
│           ├── res/
│           │   ├── layout/
│           │   │   └── activity_main.xml
│           │   └── values/
│           │       ├── strings.xml
│           │       └── themes.xml
│           └── assets/
│               └── test.html
├── build.gradle
└── settings.gradle
```

## Requirements

- Android Studio Arctic Fox (2020.3.1) or later
- Android SDK 24 (Android 7.0) or higher
- Java 8 or higher

## Build Instructions

### Option 1: Using Android Studio (Recommended)

1. **Open Project**
   ```
   Open Android Studio > File > Open > Select android_app folder
   ```

2. **Sync Gradle**
   - Android Studio will automatically sync Gradle
   - Wait for dependencies to download

3. **Build APK**
   ```
   Build > Build Bundle(s) / APK(s) > Build APK(s)
   ```

4. **Install on Device**
   - Connect Android device via USB (enable USB debugging)
   - Click "Run" (green play button) or press Shift+F10

### Option 2: Using Command Line

1. **Navigate to project directory**
   ```bash
   cd d:\Download\glasstest\android_app
   ```

2. **Build Debug APK**
   ```bash
   # Windows
   gradlew.bat assembleDebug
   
   # Linux/Mac
   ./gradlew assembleDebug
   ```

3. **Install APK**
   ```bash
   # APK location: app/build/outputs/apk/debug/app-debug.apk
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

## Usage

1. **Launch App**: Open "Glass Test" from app drawer
2. **Video Playback**: YouTube video starts automatically
3. **Monitor**: App logs video quality, stalls, and network metrics
4. **Download Logs**: Tap "Download Logs" button to save
5. **Clear Logs**: Tap "Clear Logs" to reset data

## Log File Location

Logs are saved to:
```
/storage/emulated/0/Android/data/com.glasstest/files/Download/GlassTest/
```

You can access them via:
- File manager app
- Android Studio Device File Explorer
- ADB pull command: `adb pull /sdcard/Android/data/com.glasstest/files/Download/GlassTest/`

## Permissions

The app requires:
- **INTERNET**: For YouTube API and video streaming
- **ACCESS_NETWORK_STATE**: To check network connectivity
- **WRITE_EXTERNAL_STORAGE**: To save log files (Android 9 and below)
- **READ_EXTERNAL_STORAGE**: To access saved logs (Android 12 and below)

## Customization

### Change Video ID

Edit `app/src/main/assets/test.html`:
```javascript
videoId: 'YOUR_VIDEO_ID_HERE'
```

### Adjust Log Interval

Edit `app/src/main/assets/test.html`:
```javascript
}, 500);  // Change from 500ms to desired interval
```

### Modify UI

Edit `app/src/main/res/layout/activity_main.xml` to customize layout

## Troubleshooting

### Video not playing
- Check internet connection
- Verify YouTube video ID is valid
- Enable "Use cleartext traffic" in AndroidManifest.xml

### Logs not saving
- Check storage permissions
- Verify app has write access
- Check logcat for error messages: `adb logcat *:E`

### WebView errors
- Clear app data: Settings > Apps > Glass Test > Clear Data
- Update WebView: Play Store > System WebView

## Building Release APK

1. **Generate Signing Key**
   ```bash
   keytool -genkey -v -keystore glasstest.keystore -alias glasstest -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Add to app/build.gradle**
   ```gradle
   android {
       signingConfigs {
           release {
               storeFile file("../glasstest.keystore")
               storePassword "your_password"
               keyAlias "glasstest"
               keyPassword "your_password"
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
           }
       }
   }
   ```

3. **Build Release APK**
   ```bash
   gradlew assembleRelease
   ```

## Testing

### Run on Emulator
1. Android Studio > AVD Manager
2. Create Virtual Device (Android 7.0+)
3. Run app on emulator

### Test on Physical Device
1. Enable Developer Options
2. Enable USB Debugging
3. Connect via USB
4. Run from Android Studio

## Known Issues

- Some devices may block autoplay (tap to play manually)
- 4K playback requires high-end devices
- Battery drain during long tests

## License

MIT License
