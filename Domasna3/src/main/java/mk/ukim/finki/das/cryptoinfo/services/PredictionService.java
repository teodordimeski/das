package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.dto.PredictionDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class PredictionService {

    private static final Logger logger = LoggerFactory.getLogger(PredictionService.class);
    private static final String PYTHON_FILTERS_DIR = "python_filters";
    private final ObjectMapper objectMapper = new ObjectMapper();

    public PredictionDTO getPrediction(String symbol) {
        try {
            File filtersDir = new File(PYTHON_FILTERS_DIR);
            if (!filtersDir.exists()) {
                throw new RuntimeException("Python filters directory not found: " + PYTHON_FILTERS_DIR);
            }

            File scriptFile = new File(filtersDir, "predict.py");
            if (!scriptFile.exists()) {
                throw new RuntimeException("Prediction script not found: " + scriptFile.getAbsolutePath());
            }

            // Convert symbol format (e.g., "BTC" -> "BTCUSDT")
            String fullSymbol = normalizeSymbol(symbol);

            // Build command
            String pythonCmd = System.getProperty("os.name").toLowerCase().contains("win") ? "python" : "python3";
            List<String> command = new ArrayList<>();
            command.add(pythonCmd);
            command.add(scriptFile.getAbsolutePath());
            command.add(fullSymbol);

            logger.info("Executing prediction for symbol: {} (full: {})", symbol, fullSymbol);

            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.directory(new File(System.getProperty("user.dir")));
            processBuilder.redirectErrorStream(true);

            Process process = processBuilder.start();

            // Read output (stderr is merged into stdout when redirectErrorStream(true))
            StringBuilder output = new StringBuilder();
            
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                    logger.debug("[Prediction] {}", line);
                }
            }

            int exitCode = process.waitFor();

            if (exitCode != 0) {
                String errorMsg = output.toString();
                // Try to parse JSON error from output (since stderr is redirected)
                try {
                    // Look for JSON error in output
                    int jsonStart = errorMsg.indexOf("{");
                    if (jsonStart != -1) {
                        String jsonPart = errorMsg.substring(jsonStart);
                        var errorJson = objectMapper.readTree(jsonPart);
                        if (errorJson.has("error")) {
                            throw new IllegalArgumentException(errorJson.get("error").asText());
                        }
                    }
                } catch (IllegalArgumentException e) {
                    // Re-throw IllegalArgumentException to preserve error message
                    throw e;
                } catch (Exception e) {
                    // Not JSON or parsing failed, use raw error below
                }
                throw new RuntimeException("Prediction failed with exit code: " + exitCode + "\n" + errorMsg);
            }

            // Parse JSON output
            String jsonOutput = output.toString().trim();
            logger.debug("Prediction output: {}", jsonOutput);

            // Find JSON in output (might have stderr messages before)
            int jsonStart = jsonOutput.indexOf("{");
            if (jsonStart == -1) {
                throw new RuntimeException("No JSON output from prediction script");
            }
            jsonOutput = jsonOutput.substring(jsonStart);

            PredictionDTO result = objectMapper.readValue(jsonOutput, PredictionDTO.class);
            
            // Return with the original symbol format (not the full symbol)
            result.setSymbol(symbol.toUpperCase());
            
            logger.info("Prediction completed for {}: predicted_close={}", 
                    symbol, result.getPredicted_close());

            return result;

        } catch (IllegalArgumentException e) {
            logger.error("Prediction error for {}: {}", symbol, e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Error executing prediction for {}: ", symbol, e);
            throw new RuntimeException("Failed to execute prediction: " + e.getMessage(), e);
        }
    }

    /**
     * Normalize symbol format (e.g., "BTC" -> "BTCUSDT")
     * Tries common quote assets: USDT, USDC, BUSD
     */
    private String normalizeSymbol(String symbol) {
        String upperSymbol = symbol.toUpperCase();
        
        // If already has quote asset, return as is
        if (upperSymbol.endsWith("USDT") || upperSymbol.endsWith("USDC") || 
            upperSymbol.endsWith("BUSD") || upperSymbol.endsWith("BTC") || 
            upperSymbol.endsWith("ETH")) {
            return upperSymbol;
        }
        
        // Try to find the symbol in database with common quote assets
        // Default to USDT (most common)
        return upperSymbol + "USDT";
    }
}

