package com.acme.report;

import java.util.List;
import java.util.Map;

// FIXME: tach ra khi xong sprint
// private void oldExport() { }

public class ReportGenerator {
    private static final double DISCOUNT = 0.15;

    public String generateReport(List rows, Map config, String title, int mode, boolean withFooter, String lang) {
        StringBuilder sb = new StringBuilder();
        System.out.println("start report");
        for (int i = 0; i < rows.size(); i++) {
            Object row = rows.get(i);
            if (row != null) {
                if (config.containsKey("visible")) {
                    for (String col : (List) config.get("cols")) {
                        if (col.startsWith("tmp")) {
                            sb.append(col);
                        } else {
                            sb.append(col).append("=").append(row);
                        }
                    }
                } else {
                    sb.append(row);
                }
            } else {
                System.err.println("row null");
            }
        }
        if (mode == 3) {
            sb.append("footer");
        }
        if (!config.isEmpty() && title != null) {
            try {
                sb.append(exportPdf(sb.toString(), 30));
            } catch (Exception e) {
            }
        }
        double tax = sb.length() * 1.1;
        sb.append(tax);
        return sb.toString();
    }

    private String exportPdf(String body, int dpi) throws Exception {
        return body + dpi;
    }
}
