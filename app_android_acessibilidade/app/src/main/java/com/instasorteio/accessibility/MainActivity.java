package com.instasorteio.accessibility;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_OVERLAY_PERMISSION = 101;
    private static final int REQUEST_FILE_PICKER = 102;

    private TextView tvAccessibilityStatus, tvUserCount;
    private Button btnEnableAccessibility, btnImportFile, btnStartOverlay;
    private EditText etUserList, etChunkSize, etDelayMin, etDelayMax;
    private CheckBox cbPhrases, cbEmojis;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvAccessibilityStatus = findViewById(R.id.tvAccessibilityStatus);
        tvUserCount = findViewById(R.id.tvUserCount);
        btnEnableAccessibility = findViewById(R.id.btnEnableAccessibility);
        btnImportFile = findViewById(R.id.btnImportFile);
        btnStartOverlay = findViewById(R.id.btnStartOverlay);
        etUserList = findViewById(R.id.etUserList);
        etChunkSize = findViewById(R.id.etChunkSize);
        etDelayMin = findViewById(R.id.etDelayMin);
        etDelayMax = findViewById(R.id.etDelayMax);
        cbPhrases = findViewById(R.id.cbPhrases);
        cbEmojis = findViewById(R.id.cbEmojis);

        btnEnableAccessibility.setOnClickListener(v -> {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
            Toast.makeText(this, "Encontre 'InstaSorteio Auto' e ative!", Toast.LENGTH_LONG).show();
        });

        btnImportFile.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("text/plain");
            startActivityForResult(intent, REQUEST_FILE_PICKER);
        });

        etUserList.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int count, int after) {
                updateUsersCount();
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        btnStartOverlay.setOnClickListener(v -> {
            if (!checkOverlayPermission()) {
                requestOverlayPermission();
                return;
            }

            if (InstagramAccessibilityService.instance == null) {
                Toast.makeText(this, "⚠️ Ative a Acessibilidade nas configurações primeiro!", Toast.LENGTH_LONG).show();
                Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                startActivity(intent);
                return;
            }

            saveConfigFromUI();

            if (CommentConfig.getInstance().usersList.isEmpty()) {
                Toast.makeText(this, "⚠️ Cole ou importe a sua lista de amigos (@)!", Toast.LENGTH_LONG).show();
                return;
            }

            // Inicia o menu flutuante
            startService(new Intent(this, FloatingWidgetService.class));

            // Abre o Instagram oficial
            try {
                Intent instaIntent = getPackageManager().getLaunchIntentForPackage("com.instagram.android");
                if (instaIntent != null) {
                    startActivity(instaIntent);
                } else {
                    Toast.makeText(this, "Abra o aplicativo do Instagram no post do sorteio!", Toast.LENGTH_LONG).show();
                }
            } catch (Exception e) {
                Toast.makeText(this, "Abra o Instagram oficial no post do sorteio!", Toast.LENGTH_LONG).show();
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        checkAccessibilityStatus();
    }

    private void checkAccessibilityStatus() {
        if (InstagramAccessibilityService.instance != null) {
            tvAccessibilityStatus.setText("Status: ✓ Acessibilidade ATIVADA!");
            tvAccessibilityStatus.setTextColor(getResources().getColor(R.color.success_green));
            btnEnableAccessibility.setVisibility(View.GONE);
        } else {
            tvAccessibilityStatus.setText("Status: ✗ Acessibilidade DESATIVADA");
            tvAccessibilityStatus.setTextColor(getResources().getColor(R.color.danger_red));
            btnEnableAccessibility.setVisibility(View.VISIBLE);
        }
    }

    private boolean checkOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return Settings.canDrawOverlays(this);
        }
        return true;
    }

    private void requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(intent, REQUEST_OVERLAY_PERMISSION);
            Toast.makeText(this, "Permita sobrepor a outros apps para exibir o menu flutuante", Toast.LENGTH_LONG).show();
        }
    }

    private void updateUsersCount() {
        String text = etUserList.getText().toString();
        List<String> list = parseUserHandles(text);
        tvUserCount.setText(list.size() + " amigos");
    }

    private List<String> parseUserHandles(String content) {
        List<String> list = new ArrayList<>();
        if (content == null || content.trim().isEmpty()) return list;

        Pattern pattern = Pattern.compile("@([a-zA-Z0-9._]+)");
        Matcher matcher = pattern.matcher(content);
        while (matcher.find()) {
            String handle = "@" + matcher.group(1).toLowerCase().trim();
            if (!list.contains(handle)) {
                list.add(handle);
            }
        }
        if (list.isEmpty()) {
            String[] words = content.split("\\s+");
            for (String w : words) {
                if (w.length() > 2) {
                    String handle = w.startsWith("@") ? w.toLowerCase() : "@" + w.toLowerCase();
                    if (!list.contains(handle)) {
                        list.add(handle);
                    }
                }
            }
        }
        return list;
    }

    private void saveConfigFromUI() {
        CommentConfig cfg = CommentConfig.getInstance();
        cfg.usersList = parseUserHandles(etUserList.getText().toString());
        try {
            cfg.chunkSize = Integer.parseInt(etChunkSize.getText().toString().trim());
            cfg.delayMin = Integer.parseInt(etDelayMin.getText().toString().trim());
            cfg.delayMax = Integer.parseInt(etDelayMax.getText().toString().trim());
        } catch (Exception e) {}
        cfg.usePhrases = cbPhrases.isChecked();
        cfg.useEmojis = cbEmojis.isChecked();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_FILE_PICKER && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            if (uri != null) {
                try {
                    InputStream is = getContentResolver().openInputStream(uri);
                    BufferedReader reader = new BufferedReader(new InputStreamReader(is));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        sb.append(line).append("\n");
                    }
                    reader.close();
                    etUserList.setText(sb.toString());
                    Toast.makeText(this, "Arquivo importado com sucesso!", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(this, "Erro ao ler arquivo: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            }
        }
    }
}
