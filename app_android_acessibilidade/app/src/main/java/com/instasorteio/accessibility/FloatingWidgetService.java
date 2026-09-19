package com.instasorteio.accessibility;

import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

public class FloatingWidgetService extends Service {

    public static FloatingWidgetService instance;
    private WindowManager windowManager;
    private View floatingView;
    private TextView tvStatus, tvProgress;
    private Button btnStart, btnStop;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;

        floatingView = LayoutInflater.from(this).inflate(R.layout.floating_widget_layout, null);

        int layoutFlag;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            layoutFlag = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutFlag = WindowManager.LayoutParams.TYPE_PHONE;
        }

        final WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                layoutFlag,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
        );

        params.gravity = Gravity.TOP | Gravity.START;
        params.x = 40;
        params.y = 200;

        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        windowManager.addView(floatingView, params);

        tvStatus = floatingView.findViewById(R.id.tvFloatingStatus);
        tvProgress = floatingView.findViewById(R.id.tvFloatingProgress);
        btnStart = floatingView.findViewById(R.id.btnFloatingStart);
        btnStop = floatingView.findViewById(R.id.btnFloatingStop);
        View btnClose = floatingView.findViewById(R.id.btnFloatingClose);

        updateProgress("Comentário: " + CommentConfig.getInstance().currentIndex + "/" + CommentConfig.getInstance().getTotalChunks());

        btnStart.setOnClickListener(v -> {
            CommentConfig config = CommentConfig.getInstance();
            if (config.usersList.isEmpty()) {
                Toast.makeText(this, "Adicione amigos na lista primeiro!", Toast.LENGTH_SHORT).show();
                return;
            }
            if (InstagramAccessibilityService.instance == null) {
                Toast.makeText(this, "Ative a Acessibilidade nas configurações!", Toast.LENGTH_LONG).show();
                return;
            }

            config.isRunning = true;
            btnStart.setEnabled(false);
            btnStop.setEnabled(true);
            updateStatus("Iniciando...");
            InstagramAccessibilityService.instance.triggerNextComment();
        });

        btnStop.setOnClickListener(v -> {
            CommentConfig.getInstance().isRunning = false;
            btnStart.setEnabled(true);
            btnStop.setEnabled(false);
            updateStatus("Pausado");
        });

        btnClose.setOnClickListener(v -> stopSelf());

        // Tornar a janela flutuante arrastável com o dedo
        floatingView.findViewById(R.id.floatingRoot).setOnTouchListener(new View.OnTouchListener() {
            private int initialX, initialY;
            private float initialTouchX, initialTouchY;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x;
                        initialY = params.y;
                        initialTouchX = event.getRawX();
                        initialTouchY = event.getRawY();
                        return true;

                    case MotionEvent.ACTION_MOVE:
                        params.x = initialX + (int) (event.getRawX() - initialTouchX);
                        params.y = initialY + (int) (event.getRawY() - initialTouchY);
                        windowManager.updateViewLayout(floatingView, params);
                        return true;
                }
                return false;
            }
        });
    }

    public void updateStatus(String status) {
        if (tvStatus != null) {
            tvStatus.post(() -> tvStatus.setText(status));
        }
    }

    public void updateProgress(String progress) {
        if (tvProgress != null) {
            tvProgress.post(() -> tvProgress.setText(progress));
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        if (floatingView != null && windowManager != null) {
            windowManager.removeView(floatingView);
        }
    }
}
