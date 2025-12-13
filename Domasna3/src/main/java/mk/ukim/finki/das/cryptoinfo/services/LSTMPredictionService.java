package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.dto.LSTMPredictionDTO;
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
public class LSTMPredictionService {

    private static final Logger logger = LoggerFactory.getLogger(LSTMPredictionService.class);
    private static final String PYTHON_FILTERS_DIR = "python_filters";
    private final ObjectMapper objectMapper = new ObjectMapper();

    public LSTMPredictionDTO getLSTMPrediction(String symbol, Integer lookbackPeriod, Integer predictionDays) {
        try {
            File filtersDir = new File(PYTHON_FILTERS_DIR);
            if (!filtersDir.exists()) {
                throw new RuntimeException("Python filters directory not found: " + PYTHON_FILTERS_DIR);
            }

            File scriptFile = new File(filtersDir, "LSTMPredictor.py");
            if (!scriptFile.exists()) {
                throw new RuntimeException("LSTM script not found: " + scriptFile.getAbsolutePath());
            }

            // Build command
            String pythonCmd = System.getProperty("os.name").toLowerCase().contains("win") ? "python" : "python3";
            List<String> command = new ArrayList<>();
            command.add(pythonCmd);
            command.add(scriptFile.getAbsolutePath());
            command.add(symbol);
            
            if (lookbackPeriod != null) {
                command.add(lookbackPeriod.toString());
            }
            if (predictionDays != null) {
                command.add(predictionDays.toString());
            }

            logger.info("Executing LSTM prediction for symbol: {}, lookback: {}, days: {}", 
                    symbol, lookbackPeriod, predictionDays);

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
                    logger.debug("[LSTM] {}", line);
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
                throw new RuntimeException("LSTM prediction failed with exit code: " + exitCode + "\n" + errorMsg);
            }

            // Parse JSON output
            String jsonOutput = output.toString().trim();
            logger.debug("LSTM output: {}", jsonOutput);

            // Find JSON in output (might have stderr messages before)
            int jsonStart = jsonOutput.indexOf("{");
            if (jsonStart == -1) {
                throw new RuntimeException("No JSON output from LSTM script");
            }
            jsonOutput = jsonOutput.substring(jsonStart);

            LSTMPredictionDTO result = objectMapper.readValue(jsonOutput, LSTMPredictionDTO.class);
            logger.info("LSTM prediction completed for {}: RMSE={}, MAPE={}, R2={}", 
                    symbol, result.getMetrics().getRmse(), 
                    result.getMetrics().getMape(), 
                    result.getMetrics().getR2Score());

            return result;

        } catch (IllegalArgumentException e) {
            logger.error("LSTM prediction error for {}: {}", symbol, e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Error executing LSTM prediction for {}: ", symbol, e);
            throw new RuntimeException("Failed to execute LSTM prediction: " + e.getMessage(), e);
        }
    }
}

