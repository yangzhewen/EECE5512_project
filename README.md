# Glass Test - Network Measurement Toolkit

Comprehensive network performance measurement toolkit, including video streaming tests, bandwidth measurement, and YouTube video quality monitoring.

## Components

### 1. YouTube Video Quality Monitor (test.html / testLive.html)

HTML pages for monitoring YouTube video playback quality and network performance.

**Features:**
- Auto-play and record video quality
- Detect video stalls
- Record quality changes
- Monitor buffer health
- Auto-download logs (every 2-5 minutes)

**Usage:**
```bash
# Start local HTTP server using Python
python -m http.server 8000

# Open in browser
http://localhost:8000/test.html
```

**Log Fields:**
- `type`: Log type (periodic, state_change, quality_change, stall)
- `quality`: Current quality (hd720, hd1080, hd1440, hd2160, etc.)
- `timeSec`: Current playback time
- `loadedFraction`: Buffered percentage
- `bytesLoaded/bytesTotal`: Loaded/total bytes
- `totalStalls`: Total stall count
- `totalStallDuration`: Total stall duration (milliseconds)
- `liveLatency`: Live stream latency (seconds) - testLive.html only

### 2. Caddy-style HTTP Server (caddy_server.py)

Modern HTTP/HTTPS server, similar to Caddy.

**Usage:**
```bash
# Start HTTP server
python caddy_server.py

# Specify port and directory
python caddy_server.py -p 8080 -d ./public

# Enable HTTPS
python caddy_server.py --https --cert cert.pem --key key.pem

# Disable CORS
python caddy_server.py --no-cors
```

**Features:**
- Static file serving
- CORS support
- File browser
- Status endpoints
- File upload support
- HTTPS support

**API Endpoints:**
- `GET /` - Static file serving
- `GET /status` - Server status (JSON)
- `GET /health` - Health check
- `GET /browse` - File browser
- `POST /upload` - File upload

### 3. Video Streaming Server (video_server.py)

Provides video streaming services with bandwidth control.

**Usage:**
```bash
# Install dependencies
pip install flask

# Start server
python video_server.py

# Access
http://localhost:8080
```

**Features:**
- Video file listing
- Stream video
- Dynamic bandwidth limiting
- Multi-client support

**API:**
- `GET /` - Video list
- `GET /video/<filename>` - Download video
- `GET /stream/<filename>` - Stream video
- `GET /set_bandwidth/<mbps>` - Set bandwidth limit

### 4. iPerf3-compatible Tools (iperf_server.py / iperf_client.py)

Complete iPerf3-compatible implementation for network performance testing.

**Server:**
```bash
# Start TCP server
python iperf_server.py

# Start UDP server
python iperf_server.py -u

# Specify port
python iperf_server.py -p 5201
```

**Client:**
```bash
# TCP test
python iperf_client.py <server_ip>

# UDP test
python iperf_client.py <server_ip> -u

# Multi-stream parallel test
python iperf_client.py <server_ip> -P 4

# Specify bandwidth and duration
python iperf_client.py <server_ip> -u -b 50 -t 30

# Save results
python iperf_client.py <server_ip> -o results.json
```

**Parameters:**
- `-p, --port`: Server port (default: 5201)
- `-t, --time`: Test duration in seconds (default: 10)
- `-P, --parallel`: Number of parallel streams (default: 1)
- `-u, --udp`: Use UDP mode
- `-b, --bandwidth`: UDP target bandwidth (Mbps)
- `-o, --output`: Save results to JSON

### 5. Nuttcp Bandwidth Testing Tool

Network throughput measurement tool similar to iperf.

**Server:**
```bash
# Start server (listens on both TCP and UDP)
python nuttcp_server.py

# Specify port
python nuttcp_server.py -p 5001
```

**Client:**
```bash
# TCP test (default)
python nuttcp_client.py <server_ip>

# UDP test
python nuttcp_client.py <server_ip> -u

# Specify parameters
python nuttcp_client.py <server_ip> -p 5001 -t 10 -u -r 50

# Save results to JSON
python nuttcp_client.py <server_ip> -o results.json
```

**Parameters:**
- `-p, --port`: Server port (default: 5001)
- `-t, --time`: Test duration in seconds (default: 10)
- `-u, --udp`: Use UDP (default: TCP)
- `-r, --rate`: UDP target rate in Mbps (default: 10)
- `-o, --output`: Save results to JSON file

### 6. Integrated Measurement Application (measurement_app.py)

Integrates all measurement tools.

**Usage:**

**Run integrated test:**
```bash
# Basic test (60 seconds, test every 10 seconds)
python measurement_app.py test <server_ip>

# Custom parameters
python measurement_app.py test <server_ip> -d 120 -i 15 -o ./results
```

**Analyze YouTube logs:**
```bash
python measurement_app.py analyze youtube_logs_1234567890.json
```

**Features:**
- Periodic TCP/UDP bandwidth tests
- Auto-save test results
- Generate test summary
- Parse YouTube log statistics

### 7. Android Application (android_app/)

Native Android app integrating the YouTube video quality monitor.

**Features:**
- WebView integration of test.html
- JavaScript bridge for log saving
- Native download and clear buttons
- Auto-save to device storage
- Full YouTube API support

**Build Instructions:**
```bash
# Using Android Studio
1. Open Android Studio
2. File > Open > Select android_app folder
3. Wait for Gradle sync
4. Run on device or emulator

# Using command line
cd android_app
gradlew.bat assembleDebug
```

**Log Location:**
```
/sdcard/Android/data/com.glasstest/files/Download/GlassTest/
```

See `android_app/README.md` for detailed instructions.

## Directory Structure

```
glasstest/
├── test.html                  # YouTube on-demand video monitor
├── testLive.html             # YouTube live stream monitor
├── caddy_server.py           # Caddy-style HTTP/HTTPS server
├── video_server.py           # Video streaming server
├── iperf_server.py           # iPerf3-compatible server
├── iperf_client.py           # iPerf3-compatible client
├── nuttcp_server.py          # Nuttcp server
├── nuttcp_client.py          # Nuttcp client
├── measurement_app.py        # Integrated measurement application
├── android_app/              # Android application
│   ├── app/                  # Android app source code
│   ├── build.gradle          # Build configuration
│   └── README.md             # Android app documentation
├── README.md                 # This document
├── requirements.txt          # Python dependencies
├── videos/                   # Video files directory (create manually)
└── measurements/             # Measurement results output (auto-created)
```

## Common Use Cases

### Scenario 1: YouTube Video Quality Testing
1. Start local HTTP server: `python -m http.server 8000`
2. Open in browser: `http://localhost:8000/test.html`
3. Video auto-plays and logs data
4. Wait for auto-download or click "Download Logs" manually

### Scenario 2: Network Bandwidth Measurement
1. On server: `python nuttcp_server.py`
2. On client: `python nuttcp_client.py <server_ip> -t 30 -o bandwidth.json`
3. View results file: `bandwidth.json`

### Scenario 3: Comprehensive Network Performance Test
1. Server: `python nuttcp_server.py`
2. Client: `python measurement_app.py test <server_ip> -d 300 -i 30`
3. Open YouTube monitor in browser simultaneously
4. Analyze results: `python measurement_app.py analyze youtube_logs_xxx.json`

### Scenario 4: Video Streaming Service Test
1. Place video files in `videos/` directory
2. Start server: `python video_server.py`
3. Access in browser: `http://localhost:8080`
4. Set bandwidth limit: visit `http://localhost:8080/set_bandwidth/10` (10MB/s)

### Scenario 5: Mobile Testing with Android App
1. Build and install Android app
2. Launch app on device
3. Video auto-plays and logs quality metrics
4. Tap "Download Logs" to save results
5. Access logs via file manager or ADB

## Dependencies Installation

```bash
# Video server dependencies
pip install flask

# Other components use Python standard library only
```

Or install all at once:
```bash
pip install -r requirements.txt
```

## Notes

1. **Firewall Settings**: Ensure test ports (5001, 5201, 8080, etc.) are not blocked by firewall
2. **Permission Issues**: Some systems may require administrator privileges to bind ports
3. **Network Environment**: Recommended to test in stable network conditions
4. **Browser Support**: YouTube monitor pages require modern browsers (Chrome, Firefox, Edge, etc.)
5. **Log Size**: Long-duration tests generate large logs, monitor disk space
6. **Mobile Testing**: Android app requires Android 7.0+ and internet permissions

## Troubleshooting

**Issue: YouTube video doesn't auto-play**
- Check if browser allows autoplay
- Ensure network can access YouTube
- Check browser console for error messages

**Issue: Nuttcp connection failed**
- Confirm server is running
- Verify IP address and port are correct
- Check firewall settings

**Issue: Video server fails to start**
- Check Flask is installed: `pip install flask`
- Confirm port 8080 is not in use
- Create `videos/` directory

**Issue: Android app video not playing**
- Check internet connection
- Verify YouTube video ID is valid
- Clear app data and restart

**Issue: Android logs not saving**
- Check storage permissions
- Verify app has write access
- Check logcat: `adb logcat *:E`

## Performance Tips

1. **For high-quality tests**: Use 4K resolution settings in HTML files
2. **For long-duration tests**: Increase auto-download interval to reduce overhead
3. **For parallel testing**: Use iPerf3 with multiple parallel streams (`-P` option)
4. **For mobile testing**: Keep device screen on during tests to prevent throttling
5. **For accurate results**: Close other network-intensive applications

## Building Release Versions

### Android APK
```bash
# Generate signing key
keytool -genkey -v -keystore glasstest.keystore -alias glasstest -keyalg RSA -keysize 2048 -validity 10000

# Build release APK
cd android_app
gradlew assembleRelease
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License

**Usage:**

**Run integrated test:**
```bash
# Basic test (60 seconds, test every 10 seconds)
python measurement_app.py test <server_ip>

# Custom parameters
python measurement_app.py test <server_ip> -d 120 -i 15 -o ./results
```

**Analyze YouTube logs:**
```bash
python measurement_app.py analyze youtube_logs_1234567890.json
```

**Features:**
- Periodic TCP/UDP bandwidth tests
- Auto-save test results
- Generate test summary
- Parse YouTube log statistics

## 目录结构

```
glasstest/
├── test.html              # YouTube点播视频监控
├── testLive.html          # YouTube直播视频监控
├── caddy_server.py        # Caddy-style HTTP/HTTPS服务器
├── video_server.py        # 视频流服务器
├── iperf_server.py        # iPerf3兼容服务器
├── iperf_client.py        # iPerf3兼容客户端
├── nuttcp_server.py       # Nuttcp服务器
├── nuttcp_client.py       # Nuttcp客户端
├── measurement_app.py     # 集成测量应用
├── README.md              # 本文档
├── requirements.txt       # Python依赖
├── videos/                # 视频文件目录（需创建）
└── measurements/          # 测量结果输出目录（自动创建）
```

## 典型使用场景

### 场景1：YouTube视频质量测试
1. 启动本地HTTP服务器：`python -m http.server 8000`
2. 浏览器打开 `http://localhost:8000/test.html`
3. 视频自动播放并记录日志
4. 等待自动下载日志或手动点击"Download Logs"

### 场景2：网络带宽测量
1. 在服务器上运行：`python nuttcp_server.py`
2. 在客户端运行：`python nuttcp_client.py <server_ip> -t 30 -o bandwidth.json`
3. 查看结果文件 `bandwidth.json`

### 场景3：综合网络性能测试
1. 服务器端：`python nuttcp_server.py`
2. 客户端：`python measurement_app.py test <server_ip> -d 300 -i 30`
3. 同时在浏览器打开YouTube监控页面
4. 分析结果：`python measurement_app.py analyze youtube_logs_xxx.json`

### 场景4：视频流服务测试
1. 将视频文件放入 `videos/` 目录
2. 启动服务器：`python video_server.py`
3. 浏览器访问：`http://localhost:8080`
4. 设置带宽限制：访问 `http://localhost:8080/set_bandwidth/10` (10MB/s)

## 依赖安装

```bash
# 视频服务器依赖
pip install flask

# 其他组件使用Python标准库，无需额外安装
```

## 注意事项

1. **防火墙设置**：确保测试端口（5001, 8080等）未被防火墙阻挡
2. **权限问题**：某些系统可能需要管理员权限来绑定端口
3. **网络环境**：建议在稳定的网络环境下进行测试
4. **浏览器支持**：YouTube监控页面需要现代浏览器（Chrome, Firefox, Edge等）
5. **日志大小**：长时间测试会产生大量日志，注意磁盘空间

## 故障排除

**问题：YouTube视频不自动播放**
- 检查浏览器是否允许自动播放
- 确保网络可以访问YouTube
- 查看浏览器控制台错误信息

**问题：Nuttcp连接失败**
- 确认服务器已启动
- 检查IP地址和端口是否正确
- 验证防火墙设置

**问题：视频服务器启动失败**
- 检查Flask是否已安装：`pip install flask`
- 确认端口8080未被占用
- 创建 `videos/` 目录

## 许可证

MIT License
#   E E C E 5 5 1 2 _ p r o j e c t  
 