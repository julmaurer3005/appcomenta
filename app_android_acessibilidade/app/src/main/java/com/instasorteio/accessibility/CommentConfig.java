package com.instasorteio.accessibility;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public class CommentConfig {
    private static CommentConfig instance;

    public List<String> usersList = new ArrayList<>();
    public int chunkSize = 3;
    public int delayMin = 45;
    public int delayMax = 85;
    public int batchSize = 5;         // Pausa a cada X comentários
    public int batchPause = 300;       // Duração da pausa em segundos (ex: 5 min)
    public boolean usePhrases = true;
    public boolean useEmojis = true;

    public boolean isRunning = false;
    public int currentIndex = 0;

    public List<String> phrases = Arrays.asList(
        "Boa sorte!", "Tomara que eu ganhe!", "Sorteia eu!",
        "Dedos cruzados!", "Tô na torcida!", "Já é meu!",
        "Quero muito ganhar!", "Vem sorte!", "Na torcida aqui!",
        "Bora ganhar!", "Agora vai!", "Fé no prêmio!",
        "Se Deus quiser!", "Confiante!", "Essa vitória é nossa!"
    );

    public List<String> emojis = Arrays.asList("🍀", "🤞", "✨", "🔥", "🙌", "🎯", "⭐", "🎉");

    private CommentConfig() {}

    public static synchronized CommentConfig getInstance() {
        if (instance == null) {
            instance = new CommentConfig();
        }
        return instance;
    }

    public String generateCommentForCurrentIndex() {
        if (usersList.isEmpty() || currentIndex >= getTotalChunks()) {
            return null;
        }

        int start = currentIndex * chunkSize;
        int end = Math.min(start + chunkSize, usersList.size());
        List<String> chunk = usersList.subList(start, end);

        StringBuilder sb = new StringBuilder();
        for (String user : chunk) {
            sb.append(user).append(" ");
        }

        Random rnd = new Random();
        if (usePhrases && !phrases.isEmpty()) {
            sb.append(phrases.get(rnd.nextInt(phrases.size()))).append(" ");
        }

        if (useEmojis && !emojis.isEmpty()) {
            sb.append(emojis.get(rnd.nextInt(emojis.size())));
        }

        return sb.toString().trim();
    }

    public int getTotalChunks() {
        if (usersList.isEmpty() || chunkSize <= 0) return 0;
        return (int) Math.ceil((double) usersList.size() / chunkSize);
    }

    public int getNextDelay() {
        if (batchSize > 0 && currentIndex > 0 && currentIndex % batchSize == 0) {
            return Math.max(batchPause, 60);
        }

        if (delayMax <= delayMin) {
            return Math.max(delayMin, 5);
        }
        Random rnd = new Random();
        return rnd.nextInt((delayMax - delayMin) + 1) + delayMin;
    }

    public boolean isBatchPause() {
        return (batchSize > 0 && currentIndex > 0 && currentIndex % batchSize == 0);
    }
}
