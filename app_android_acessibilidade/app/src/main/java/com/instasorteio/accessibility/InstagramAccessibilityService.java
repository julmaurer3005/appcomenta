package com.instasorteio.accessibility;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.content.Intent;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.List;

public class InstagramAccessibilityService extends AccessibilityService {

    private static final String TAG = "InstaSorteioService";
    public static InstagramAccessibilityService instance;
    private Handler handler;
    private boolean isPosting = false;
    private String pendingCommentText = null;
    private int retryCount = 0;

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
        isPosting = false;
    }

    @Override
    public boolean onUnbind(Intent intent) {
        instance = null;
        isPosting = false;
        return super.onUnbind(intent);
    }

    // Executa o próximo comentário
    public void triggerNextComment() {
        if (isPosting) return;

        CommentConfig config = CommentConfig.getInstance();
        if (!config.isRunning) return;

        if (config.currentIndex >= config.getTotalChunks()) {
            config.isRunning = false;
            pendingCommentText = null;
            updateFloatingStatus("🎉 Sorteio Concluído!");
            updateFloatingProgress();
            return;
        }

        // Mantém o texto atual para evitar ficar sorteando novas frases em loop caso dê retry
        if (pendingCommentText == null) {
            pendingCommentText = config.generateCommentForCurrentIndex();
        }

        if (pendingCommentText == null) {
            config.isRunning = false;
            updateFloatingStatus("Sem mais comentários!");
            return;
        }

        isPosting = true;
        updateFloatingStatus("Localizando campo...");

        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) {
            isPosting = false;
            scheduleRetry(2500);
            return;
        }

        AccessibilityNodeInfo commentBox = findCommentBox(rootNode);

        // Se não encontrou campo de digitação, tenta abrir a aba de comentários no post
        if (commentBox == null) {
            AccessibilityNodeInfo triggerBtn = findCommentTriggerOnPost(rootNode);
            if (triggerBtn != null) {
                updateFloatingStatus("Abrindo comentários...");
                clickNode(triggerBtn);
                isPosting = false;
                scheduleRetry(1800);
                return;
            }

            isPosting = false;
            updateFloatingStatus("⚠️ Abra o post no Instagram");
            scheduleRetry(3500);
            return;
        }

        // Campo de comentário encontrado! Foca e insere o texto
        updateFloatingStatus("Digitando comentário...");
        commentBox.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        commentBox.performAction(AccessibilityNodeInfo.ACTION_CLICK);

        Bundle arguments = new Bundle();
        arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, pendingCommentText);
        commentBox.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);

        // Aguarda 1.5s para o Instagram habilitar e renderizar o botão Publicar / Enviar
        handler.postDelayed(() -> {
            if (!config.isRunning) {
                isPosting = false;
                return;
            }

            AccessibilityNodeInfo newRoot = getRootInActiveWindow();
            AccessibilityNodeInfo newCommentBox = newRoot != null ? findCommentBox(newRoot) : null;
            AccessibilityNodeInfo postBtn = newRoot != null ? findPostButton(newRoot, newCommentBox) : null;

            boolean sent = false;
            if (postBtn != null) {
                sent = clickNode(postBtn);
            }

            // Fallbacks de envio caso o botão do layout do Instagram use evento customizado
            if (!sent && newCommentBox != null) {
                // 1. Tenta acionar a ação Enter do teclado (IME) no Android 11+ (API 30+)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    try {
                        sent = newCommentBox.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.getId());
                    } catch (Exception ignored) {}
                }

                // 2. Tenta clique por coordenadas no canto direito do campo (botão publicar/enviar)
                if (!sent) {
                    Rect cbBounds = new Rect();
                    newCommentBox.getBoundsInScreen(cbBounds);
                    int screenWidth = getResources().getDisplayMetrics().widthPixels;
                    clickLocation(screenWidth - 60, cbBounds.centerY());
                    sent = true;
                }
            }

            if (sent) {
                retryCount = 0;
                config.currentIndex++;
                pendingCommentText = null; // Libera para gerar o próximo na próxima rodada
                updateFloatingProgress();
                updateFloatingStatus("✅ Postado com Sucesso!");

                isPosting = false;

                if (config.currentIndex >= config.getTotalChunks()) {
                    config.isRunning = false;
                    updateFloatingStatus("🎉 Sorteio Concluído!");
                    return;
                }

                // Agenda o próximo comentário (delay normal ou pausa do lote)
                int delay = config.getNextDelay();
                boolean isBatch = config.isBatchPause();
                scheduleCountdown(delay, isBatch);
            } else {
                isPosting = false;
                retryCount++;
                if (retryCount >= 3) {
                    updateFloatingStatus("⚠️ Toque em Publicar manualmente");
                } else {
                    updateFloatingStatus("⚠️ Tentando enviar...");
                }
                scheduleRetry(3000);
            }
        }, 1500);
    }

    private AccessibilityNodeInfo findCommentBox(AccessibilityNodeInfo node) {
        if (node == null) return null;

        CharSequence className = node.getClassName();
        if (className != null && (className.toString().contains("EditText") || node.isEditable())) {
            return node;
        }

        CharSequence text = node.getText();
        CharSequence hint = node.getContentDescription();
        String textStr = text != null ? text.toString().toLowerCase() : "";
        String hintStr = hint != null ? hint.toString().toLowerCase() : "";

        if (textStr.contains("coment") || textStr.contains("comment") ||
            hintStr.contains("coment") || hintStr.contains("comment") ||
            textStr.contains("mensagem") || hintStr.contains("mensagem")) {
            if (node.isFocusable() || node.isClickable() || node.isEditable()) {
                return node;
            }
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findCommentBox(child);
            if (res != null) return res;
        }

        return null;
    }

    private AccessibilityNodeInfo findCommentTriggerOnPost(AccessibilityNodeInfo node) {
        if (node == null) return null;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();
        String resId = node.getViewIdResourceName();

        String textStr = text != null ? text.toString().toLowerCase() : "";
        String descStr = desc != null ? desc.toString().toLowerCase() : "";
        String resIdStr = resId != null ? resId.toLowerCase() : "";

        boolean matchDesc = descStr.contains("comentar") || descStr.contains("comentário") || descStr.contains("comment");
        boolean matchText = textStr.contains("adicione um comentário") || textStr.contains("adicionar comentário") ||
                            textStr.contains("ver todos") || textStr.contains("view all") || textStr.contains("add a comment");
        boolean matchId = resIdStr.contains("comment_button") || resIdStr.contains("ufi_comment") ||
                          resIdStr.contains("button_comment") || resIdStr.contains("row_feed_button_comment");

        if ((matchDesc || matchText || matchId) && (node.isClickable() || node.getParent() != null)) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = findCommentTriggerOnPost(child);
            if (res != null) return res;
        }

        return null;
    }

    private AccessibilityNodeInfo findPostButton(AccessibilityNodeInfo node, AccessibilityNodeInfo commentBox) {
        if (node == null) return null;

        AccessibilityNodeInfo explicitBtn = searchExplicitPostButton(node);
        if (explicitBtn != null) {
            return explicitBtn;
        }

        if (commentBox != null) {
            Rect cbBounds = new Rect();
            commentBox.getBoundsInScreen(cbBounds);
            return searchNeighborButton(node, cbBounds);
        }

        return null;
    }

    private AccessibilityNodeInfo searchExplicitPostButton(AccessibilityNodeInfo node) {
        if (node == null) return null;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();
        String resId = node.getViewIdResourceName();

        String textStr = text != null ? text.toString().toLowerCase().trim() : "";
        String descStr = desc != null ? desc.toString().toLowerCase().trim() : "";
        String resIdStr = resId != null ? resId.toLowerCase() : "";

        boolean isMatch = false;

        // Texto
        if (textStr.equals("publicar") || textStr.equals("post") || textStr.equals("postar") ||
            textStr.equals("enviar") || textStr.equals("send") || textStr.contains("publicar") ||
            textStr.contains("post comment") || textStr.contains("publicar comentário")) {
            isMatch = true;
        }

        // Descrição de Acessibilidade
        if (descStr.contains("publicar") || descStr.contains("postar") || descStr.contains("post") ||
            descStr.contains("enviar") || descStr.contains("send") || descStr.contains("publicar comentário") ||
            descStr.contains("enviar mensagem") || descStr.contains("send message")) {
            isMatch = true;
        }

        // ID de recurso Android
        if (resIdStr.contains("post_button") || resIdStr.contains("comment_post") ||
            resIdStr.contains("button_post") || resIdStr.contains("layout_comment_thread_post_button") ||
            resIdStr.contains("row_comment_post_button") || resIdStr.contains("row_thread_button_send") ||
            resIdStr.contains("direct_text_send_button") || resIdStr.contains("send_button") ||
            resIdStr.contains("action_button") || resIdStr.contains("inline_composer_action_button")) {
            isMatch = true;
        }

        if (isMatch && (node.isClickable() || node.getParent() != null)) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = searchExplicitPostButton(child);
            if (res != null) return res;
        }

        return null;
    }

    private AccessibilityNodeInfo searchNeighborButton(AccessibilityNodeInfo node, Rect cbBounds) {
        if (node == null) return null;

        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);

        if (bounds.left >= cbBounds.right - 20 &&
            bounds.centerY() >= cbBounds.top - 50 &&
            bounds.centerY() <= cbBounds.bottom + 50 &&
            bounds.width() > 10 && bounds.height() > 10 &&
            node.isClickable()) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo res = searchNeighborButton(child, cbBounds);
            if (res != null) return res;
        }

        return null;
    }

    private boolean clickNode(AccessibilityNodeInfo node) {
        if (node == null) return false;

        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);

        boolean performed = false;

        if (node.isClickable()) {
            performed = node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        }

        if (!performed) {
            AccessibilityNodeInfo parent = node.getParent();
            while (parent != null) {
                if (parent.isClickable()) {
                    performed = parent.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    break;
                }
                parent = parent.getParent();
            }
        }

        if (bounds.width() > 0 && bounds.height() > 0) {
            clickLocation(bounds.centerX(), bounds.centerY());
            performed = true;
        }

        return performed;
    }

    private void clickLocation(float x, float y) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            GestureDescription.Builder builder = new GestureDescription.Builder();
            Path path = new Path();
            path.moveTo(x, y);
            builder.addStroke(new GestureDescription.StrokeDescription(path, 0, 50));
            dispatchGesture(builder.build(), null, null);
        }
    }

    private void scheduleRetry(int delayMs) {
        handler.postDelayed(() -> {
            if (CommentConfig.getInstance().isRunning) {
                triggerNextComment();
            }
        }, delayMs);
    }

    private void scheduleCountdown(int seconds, boolean isBatchPause) {
        final int[] remaining = {seconds};
        final String prefix = isBatchPause ? "☕ Pausa do lote: " : "⏳ Próximo em: ";

        Runnable countdownRunnable = new Runnable() {
            @Override
            public void run() {
                if (!CommentConfig.getInstance().isRunning) return;

                if (remaining[0] > 0) {
                    int mins = remaining[0] / 60;
                    int secs = remaining[0] % 60;
                    String timeStr = (mins > 0) ? (mins + "m " + secs + "s") : (secs + "s");

                    updateFloatingStatus(prefix + timeStr);
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
