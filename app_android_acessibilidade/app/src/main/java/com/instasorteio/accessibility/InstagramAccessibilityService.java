package com.instasorteio.accessibility;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.Toast;

import java.util.List;
import java.util.Random;

public class InstagramAccessibilityService extends AccessibilityService {

    private static final String TAG = "InstaSorteioService";
    public static InstagramAccessibilityService instance;
    private Handler handler;
    private boolean isPosting = false;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        handler = new Handler(Looper.getMainLooper());
        Log.d(TAG, "Serviço de Acessibilidade Conectado!");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Eventos do Instagram monitorados
    }

    @Override
    public void onInterrupt() {
        instance = null;
    }

    @Override
    public boolean onUnbind(Intent intent) {
        instance = null;
        return super.onUnbind(intent);
    }

    // Executa o próximo comentário
    public void triggerNextComment() {
        if (isPosting) return;

        CommentConfig config = CommentConfig.getInstance();
        if (!config.isRunning) return;

        final String commentText = config.generateNextComment();
        if (commentText == null) {
            config.isRunning = false;
            updateFloatingStatus("Sorteio Concluído!");
            return;
        }

        isPosting = true;
        updateFloatingStatus("Procurando campo...");

        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) {
            isPosting = false;
            scheduleRetry(3000);
            return;
        }

        // Localiza a caixa de comentários
        AccessibilityNodeInfo commentBox = findCommentBox(rootNode);

        if (commentBox != null) {
            updateFloatingStatus("Digitando...");
            
            // Simula clique no campo
            commentBox.performAction(AccessibilityNodeInfo.ACTION_CLICK);

            // Insere o texto humanizado
            Bundle arguments = new Bundle();
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, commentText);
            commentBox.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);

            // Aguarda 1.5s e clica em Publicar
            handler.postDelayed(() -> {
                AccessibilityNodeInfo newRoot = getRootInActiveWindow();
                if (newRoot != null) {
                    AccessibilityNodeInfo postBtn = findPostButton(newRoot);
                    if (postBtn != null) {
                        postBtn.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        config.currentIndex++;
                        updateFloatingProgress();
                        updateFloatingStatus("✅ Postado com Sucesso!");

                        // Agenda o próximo comentário com delay aleatório
                        Random rnd = new Random();
                        int delay = rnd.nextInt((config.delayMax - config.delayMin) + 1) + config.delayMin;
                        isPosting = false;
                        scheduleCountdown(delay);
                    } else {
                        isPosting = false;
                        scheduleRetry(4000);
                    }
                } else {
                    isPosting = false;
                    scheduleRetry(4000);
                }
            }, 1500);

        } else {
            isPosting = false;
            updateFloatingStatus("Abra o post do sorteio!");
            scheduleRetry(4000);
        }
    }

    private AccessibilityNodeInfo findCommentBox(AccessibilityNodeInfo node) {
        if (node == null) return null;

        // Procura por classe EditText ou texto "Adicione um comentário" / "Comment"
        if ("android.widget.EditText".equals(node.getClassName())) {
            return node;
        }

        CharSequence text = node.getText();
        CharSequence hint = node.getContentDescription();
        if (text != null && (text.toString().contains("Adicione um comentário") || text.toString().contains("Comment"))) {
            return node;
        }
        if (hint != null && (hint.toString().contains("Adicione um comentário") || hint.toString().contains("Comment"))) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findCommentBox(child);
            if (res != null) return res;
        }

        return null;
    }

    private AccessibilityNodeInfo findPostButton(AccessibilityNodeInfo node) {
        if (node == null) return null;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();

        if (text != null && ("Publicar".equalsIgnoreCase(text.toString()) || "Post".equalsIgnoreCase(text.toString()))) {
            return node;
        }
        if (desc != null && ("Publicar".equalsIgnoreCase(desc.toString()) || "Post".equalsIgnoreCase(desc.toString()))) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findPostButton(child);
            if (res != null) return res;
        }

        return null;
    }

    private void scheduleRetry(int delayMs) {
        handler.postDelayed(() -> {
            if (CommentConfig.getInstance().isRunning) {
                triggerNextComment();
            }
        }, delayMs);
    }

    private void scheduleCountdown(int seconds) {
        final int[] remaining = {seconds};
        Runnable countdownRunnable = new Runnable() {
            @Override
            public void run() {
                if (!CommentConfig.getInstance().isRunning) return;

                if (remaining[0] > 0) {
                    updateFloatingStatus("⏳ Próximo em: " + remaining[0] + "s");
                    remaining[0]--;
                    handler.postDelayed(this, 1000);
                } else {
                    triggerNextComment();
                }
            }
        };
        handler.post(countdownRunnable);
    }

    private void updateFloatingStatus(String status) {
        if (FloatingWidgetService.instance != null) {
            FloatingWidgetService.instance.updateStatus(status);
        }
    }

    private void updateFloatingProgress() {
        if (FloatingWidgetService.instance != null) {
            CommentConfig cfg = CommentConfig.getInstance();
            FloatingWidgetService.instance.updateProgress("Comentário: " + cfg.currentIndex + "/" + cfg.getTotalChunks());
        }
    }
}
