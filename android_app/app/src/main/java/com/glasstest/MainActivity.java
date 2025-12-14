package com.glasstest;

import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.webkit.ConsoleMessage;
import android.webkit.DownloadListener;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private Button btnDownload;
    private Button btnClear;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        btnDownload = findViewById(R.id.btnDownload);
        btnClear = findViewById(R.id.btnClear);

        setupWebView();
        setupButtons();
    }

    private void setupWebView() {
        WebSettings webSettings = webView.getSettings();
        
        // Enable JavaScript
        webSettings.setJavaScriptEnabled(true);
        
        // Enable DOM storage for YouTube API
        webSettings.setDomStorageEnabled(true);
        
        // Enable database
        webSettings.setDatabaseEnabled(true);
        
        // Enable media playback
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        
        // Mixed content mode
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        
        // Cache settings
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webSettings.setAppCacheEnabled(true);
        
        // Add JavaScript interface for downloading logs
        webView.addJavascriptInterface(new WebAppInterface(this), "Android");
        
        // Set WebViewClient
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                // Inject download function override
                injectDownloadFunction();
            }
        });
        
        // Set WebChromeClient for console logging
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                android.util.Log.d("WebView", consoleMessage.message() + 
                    " -- From line " + consoleMessage.lineNumber() + 
                    " of " + consoleMessage.sourceId());
                return true;
            }
        });
        
        // Load the HTML file from assets
        webView.loadUrl("file:///android_asset/test.html");
    }

    private void setupButtons() {
        btnDownload.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Call JavaScript downloadLogs function
                webView.evaluateJavascript("downloadLogs();", null);
            }
        });

        btnClear.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Clear logs by reloading
                webView.evaluateJavascript("logs = []; console.log('Logs cleared');", null);
                Toast.makeText(MainActivity.this, "Logs cleared", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void injectDownloadFunction() {
        String script = 
            "(function() {" +
            "    var originalDownload = window.downloadLogs;" +
            "    window.downloadLogs = function() {" +
            "        var logsJson = JSON.stringify(logs, null, 2);" +
            "        Android.saveLog(logsJson);" +
            "    };" +
            "})();";
        webView.evaluateJavascript(script, null);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    // JavaScript Interface
    public class WebAppInterface {
        Context context;

        WebAppInterface(Context c) {
            context = c;
        }

        @JavascriptInterface
        public void saveLog(String logData) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    saveLogToFile(logData);
                }
            });
        }
    }

    private void saveLogToFile(String logData) {
        try {
            // Create filename with timestamp
            String timestamp = String.valueOf(System.currentTimeMillis());
            String filename = "youtube_logs_" + timestamp + ".json";
            
            // For Android 10+, use app-specific storage
            File downloadsDir = new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "GlassTest");
            if (!downloadsDir.exists()) {
                downloadsDir.mkdirs();
            }
            
            File file = new File(downloadsDir, filename);
            
            FileOutputStream fos = new FileOutputStream(file);
            fos.write(logData.getBytes());
            fos.close();
            
            Toast.makeText(this, "Log saved: " + file.getAbsolutePath(), Toast.LENGTH_LONG).show();
            
        } catch (IOException e) {
            e.printStackTrace();
            Toast.makeText(this, "Error saving log: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
}
