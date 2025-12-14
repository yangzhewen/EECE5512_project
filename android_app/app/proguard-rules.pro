# ProGuard rules for Glass Test

# Keep JavaScript interface
-keepclassmembers class com.glasstest.MainActivity$WebAppInterface {
    public *;
}

# Keep WebView JavaScript interface
-keepattributes JavascriptInterface
-keep class android.webkit.JavascriptInterface { *; }

# Keep WebView classes
-keep class android.webkit.** { *; }
