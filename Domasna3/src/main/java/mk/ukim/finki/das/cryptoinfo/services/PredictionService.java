package mk.ukim.finki.das.cryptoinfo.services;

import mk.ukim.finki.das.cryptoinfo.dto.PredictionDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
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
    private final String pythonCmd;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public PredictionService(@Value("${python.command:python3}") String pythonCmd) {
        this.pythonCmd = pythonCmd;
    }

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

            String fullSymbol = normalizeSymbol(symbol);

            List<String> command = new ArrayList<>();
            command.add(this.pythonCmd);
            command.add(scriptFile.getAbsolutePath());
            command.add(fullSymbol);

            logger.info("Executing prediction for symbol: {} (full: {})", symbol, fullSymbol);

            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.directory(new File(System.getProperty("user.dir")));
            processBuilder.redirectErrorStream(true);

            Process process = processBuilder.start();

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
                logger.error("Prediction script failed with exit code {} for symbol: {}", exitCode, symbol);
                logger.error("Script output: {}", errorMsg);
                
                try {
                    int jsonStart = errorMsg.indexOf("{");
                    if (jsonStart != -1) {
                        String jsonPart = errorMsg.substring(jsonStart);
                        var errorJson = objectMapper.readTree(jsonPart);
                        if (errorJson.has("error")) {
                            String errorMessage = errorJson.get("error").asText();
                            logger.error("Parsed error from script: {}", errorMessage);
                            throw new IllegalArgumentException(errorMessage);
                        }
                    }
                } catch (IllegalArgumentException e) {
                    throw e;
                } catch (Exception e) {
                    logger.error("Failed to parse error JSON: {}", e.getMessage());
                }
                throw new RuntimeException("Prediction failed with exit code: " + exitCode + "\n" + errorMsg);
            }

            String jsonOutput = output.toString().trim();
            logger.debug("Prediction output: {}", jsonOutput);

            int jsonStart = jsonOutput.indexOf("{");
            if (jsonStart == -1) {
                throw new RuntimeException("No JSON output from prediction script");
            }
            jsonOutput = jsonOutput.substring(jsonStart);

            PredictionDTO result = objectMapper.readValue(jsonOutput, PredictionDTO.class);
            
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

    private String normalizeSymbol(String symbol) {
        String upperSymbol = symbol.toUpperCase();
        
        if (upperSymbol.endsWith("USDT") || upperSymbol.endsWith("USDC") || 
            upperSymbol.endsWith("BUSD")) {
            return upperSymbol;
        }
        
        if (upperSymbol.length() > 3 && (upperSymbol.endsWith("BTC") || upperSymbol.endsWith("ETH"))) {
            return upperSymbol;
        }
        
        return upperSymbol + "USDT";
    }
}

